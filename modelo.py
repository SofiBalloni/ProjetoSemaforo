import pandas as pd
import numpy as np
import joblib
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score, f1_score
import matplotlib.pyplot as plt
import datetime
import time

# MODELO DENITIVO (vou usar apenas um deles, mas ai já dá os dois)

# Simulação de Dados Mais Realistas e MUITOS Casos

np.random.seed(42) # Para resultados reproduzíveis

num_pontos_total = 15000
intervalo_amostras_min = 5

data_simulada = []
timestamps_base = pd.to_datetime('2025-01-01 00:00:00')

for i in range(num_pontos_total):
    timestamp = timestamps_base + datetime.timedelta(minutes=i * intervalo_amostras_min)

    # Simulação de condições básicas dos sensores
    umidade = np.random.uniform(50, 100)
    temperatura = np.random.uniform(10, 30)
    agua_sensor_val = 0 # Assume 0 por padrão

    # Simula condição de "muita chuva/potencial alagamento" em ~20% dos casos
    # Nestes casos, a umidade é mais alta, temperatura mais baixa, e o sensor de água pode ligar
    is_severe_condition = np.random.rand() < 0.20

    if is_severe_condition:
        umidade = np.random.uniform(85, 100) # Umidade alta
        temperatura = np.random.uniform(10, 20) # Temperatura baixa
        # Sensor de água LIGA com alta chance SE as condições forem severas
        agua_sensor_val = 1 if np.random.rand() < 0.8 else 0 # 80% de chance de sensor de água ligar

    # Adiciona ruído ao sensor de água:
    # 3% de chance do sensor ligar por engano (falso positivo) em condições não severas
    if not is_severe_condition and np.random.rand() < 0.03:
        agua_sensor_val = 1
    # 5% de chance do sensor NÃO ligar (falso negativo) mesmo em condições severas
    if is_severe_condition and agua_sensor_val == 1 and np.random.rand() < 0.05:
        agua_sensor_val = 0


    data_simulada.append([timestamp, umidade, temperatura, agua_sensor_val])

df = pd.DataFrame(data_simulada, columns=['timestamp', 'umidade', 'temperatura', 'agua_sensor'])
df = df.sort_values('timestamp').reset_index(drop=True)

# Engenharia de Features: Adicionar Taxa de Mudança

df['delta_umidade'] = df['umidade'].diff().fillna(0)
df['delta_temperatura'] = df['temperatura'].diff().fillna(0)

# DEFINIÇÃO DA VARIÁVEL ALVO 'ALAGADO' AGORA É MAIS COMPLEXA E SEM O PERFEITO LINK COM AGUA_SENSOR (CABOU PRO FITTING)
# O Alagado será 1 APENAS se:
# - O sensor de água está ligado
# - A umidade está alta
# - A temperatura caiu significativamente
# - A umidade subiu rapidamente
# Isso força o modelo a olhar para todas as features para decidir o Alagamento.

df['Alagado'] = 0 # Inicializa tudo como 0 (Não Alagado)

# Definindo a regra para 'Alagado' ser 1
df.loc[(df['agua_sensor'] == 1) &                # Sensor de água detectou
       (df['umidade'] > 90) &                    # Umidade muito alta
       (df['delta_temperatura'] < -4) &          # Queda de temperatura de pelo menos 4 graus
       (df['delta_umidade'] > 8),                # Aumento de umidade de pelo menos 8%
       'Alagado'] = 1

# Pequena chance de ruído na própria variável ALAGADO para evitar 100% perfeito,
# mesmo que as regras acima sejam atendidas ou não
df.loc[df['Alagado'] == 1, 'Alagado'] = np.where(np.random.rand(len(df.loc[df['Alagado'] == 1])) < 0.98, 1, 0) # 2% de chance de não ser alagado mesmo com a regra
df.loc[df['Alagado'] == 0, 'Alagado'] = np.where(np.random.rand(len(df.loc[df['Alagado'] == 0])) < 0.005, 1, 0) # 0.5% de chance de ser alagado mesmo sem a regra (ruído)


print("Primeiras 5 linhas do DataFrame simulado (com Deltas, Agua Sensor e ALAGADO):")
print(df.head())
print("\nContagem de estados do Sensor de Água (0=não detectou, 1=detectou - É UMA FEATURE):")
print(df['agua_sensor'].value_counts())
print("\nContagem de classes ALAGADO (0=Não Alagado, 1=Alagado - VARIÁVEL ALVO):")
print(df['Alagado'].value_counts())


# Preparação dos Dados para Treino

X = df[['umidade', 'temperatura', 'delta_umidade', 'delta_temperatura', 'agua_sensor']]
y = df['Alagado'] # A variável alvo 'y' é a nova coluna 'Alagado'

# Mantendo test_size=0.2 e random_state=None para testes variáveis
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=None, stratify=y)


print(f"\nTamanho do conjunto de treino: {len(X_train)}")
print(f"Tamanho do conjunto de teste: {len(X_test)}")

# Treinamento da Árvore de Decisão (Modelo Original para Comparação)

print("\n Treinando Árvore de Decisão (com dados mais complexos e deltas) ")
model_dt = DecisionTreeClassifier(random_state=42, max_depth=8, class_weight='balanced')
model_dt.fit(X_train, y_train)

y_pred_dt = model_dt.predict(X_test)

print("\n Avaliação da Árvore de Decisão ")
acuracia_dt = accuracy_score(y_test, y_pred_dt)
recall_dt = recall_score(y_test, y_pred_dt)
f1_dt = f1_score(y_test, y_pred_dt)

print(f"Acurácia (Árvore de Decisão): {acuracia_dt:.4f}")
print(f"Recall (Árvore de Decisão): {recall_dt:.4f}")
print(f"F1-score (Árvore de Decisão): {f1_dt:.4f}")

print("\nRelatório de Classificação (Árvore de Decisão):\n", classification_report(y_test, y_pred_dt))
print("\nMatriz de Confusão (Árvore de Decisão):\n", confusion_matrix(y_test, y_pred_dt))

# --- 5. Treinamento e Ajuste de Hiperparâmetros do Random Forest ---

print("\n Otimizando Random Forest com GridSearchCV ")

param_grid = {
    'n_estimators': [50, 100, 150],
    'max_depth': [5, 8, 12],
    'min_samples_leaf': [1, 2, 4],
    'class_weight': ['balanced', None]
}

rf_model = RandomForestClassifier(random_state=42)

grid_search = GridSearchCV(estimator=rf_model, param_grid=param_grid,
                           cv=3, scoring='recall', verbose=1, n_jobs=-1)

grid_search.fit(X_train, y_train)

print(f"\nMelhores parâmetros encontrados: {grid_search.best_params_}")
print(f"Melhor Recall score (CV): {grid_search.best_score_:.4f}")

best_rf_model = grid_search.best_estimator_

y_pred_best_rf = best_rf_model.predict(X_test)

print("\n--- Avaliação do MELHOR Random Forest ---") # <--- AQUI COMEÇA A SAÍDA DO RANDOM FOREST
acuracia_best_rf = accuracy_score(y_test, y_pred_best_rf)
recall_best_rf = recall_score(y_test, y_pred_best_rf)
f1_best_rf = f1_score(y_test, y_pred_best_rf)

print(f"Acurácia (Melhor RF): {acuracia_best_rf:.4f}")
print(f"Recall (Melhor RF): {recall_best_rf:.4f}")
print(f"F1-score (Melhor RF): {f1_best_rf:.4f}")

print("\nRelatório de Classificação (Melhor RF):\n", classification_report(y_test, y_pred_best_rf))
print("\nMatriz de Confusão (Melhor RF):\n", confusion_matrix(y_test, y_pred_best_rf))


# Testando novas previsões com o MELHOR Random Forest (exemplo)
print("\n Testando novas previsões com o MELHOR Random Forest (exemplo) ")

def predict_with_all_features(model, umidade_atual, temperatura_atual, umidade_anterior, temperatura_anterior, agua_sensor_atual):
    delta_u = umidade_atual - umidade_anterior
    delta_t = temperatura_atual - temperatura_anterior
    return model.predict(np.array([[umidade_atual, temperatura_atual, delta_u, delta_t, agua_sensor_atual]]))[0]

# Cenário 1: Normal (sem água no sensor, tudo estável)
umidade_teste_1_atu = 70
temperatura_teste_1_atu = 25
umidade_teste_1_ant = 69
temperatura_teste_1_ant = 26
agua_sensor_teste_1 = 0
previsao_1_rf = predict_with_all_features(best_rf_model, umidade_teste_1_atu, temperatura_teste_1_atu,
                                         umidade_teste_1_ant, temperatura_teste_1_ant, agua_sensor_teste_1)
print(f"U: {umidade_teste_1_atu}%, T: {temperatura_teste_1_atu}°C, Água Sensor: {agua_sensor_teste_1} (Delta U: {umidade_teste_1_atu - umidade_teste_1_ant:.1f}, Delta T: {temperatura_teste_1_atu - temperatura_teste_1_ant:.1f}) -> Previsão: {'Alagamento' if previsao_1_rf == 1 else 'Não Alagamento'}")

# Cenário 2: Condições de Alagamento (água no sensor, umidade alta, temp caindo, umidade subindo)
umidade_teste_2_atu = 95
temperatura_teste_2_atu = 18
umidade_teste_2_ant = 80
temperatura_teste_2_ant = 25
agua_sensor_teste_2 = 1
previsao_2_rf = predict_with_all_features(best_rf_model, umidade_teste_2_atu, temperatura_teste_2_atu,
                                         umidade_teste_2_ant, temperatura_teste_2_ant, agua_sensor_teste_2)
print(f"U: {umidade_teste_2_atu}%, T: {temperatura_teste_2_atu}°C, Água Sensor: {agua_sensor_teste_2} (Delta U: {umidade_teste_2_atu - umidade_teste_2_ant:.1f}, Delta T: {temperatura_teste_2_atu - temperatura_teste_2_ant:.1f}) -> Previsão: {'Alagamento' if previsao_2_rf == 1 else 'Não Alagamento'}")

# Cenário 3: Sensor de água LIGADO, mas outras condições NÃO tão fortes (modelo tem que decidir)
# A simulação de Alagado aqui é mais complexa, então o resultado pode variar e não ser Alagamento
umidade_teste_3_atu = 80
temperatura_teste_3_atu = 22
umidade_teste_3_ant = 75
temperatura_teste_3_ant = 23
agua_sensor_teste_3 = 1
previsao_3_rf = predict_with_all_features(best_rf_model, umidade_teste_3_atu, temperatura_teste_3_atu,
                                         umidade_teste_3_ant, temperatura_teste_3_ant, agua_sensor_teste_3)
print(f"U: {umidade_teste_3_atu}%, T: {temperatura_teste_3_atu}°C, Água Sensor: {agua_sensor_teste_3} (Delta U: {umidade_teste_3_atu - umidade_teste_3_ant:.1f}, Delta T: {temperatura_teste_3_atu - temperatura_teste_3_ant:.1f}) -> Previsão: {'Alagamento' if previsao_3_rf == 1 else 'Não Alagamento'}")


# Salvar o Melhor Modelo Random Forest
modelo_definitivo = f'modelo_random_forest_alagamento_{int(time.time())}.joblib'
joblib.dump(best_rf_model, modelo_definitivo) 

print(f"\nModelo salvo com sucesso em '{modelo_definitivo}'")