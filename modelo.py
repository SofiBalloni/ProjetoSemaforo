# Modelo quase perfeito (demorei para perceber que faltava uma variavel no modelo)
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

# Simulação de Dados Mais Realistas e MUUUUUUUUUUUUUUUITOS Casos 

np.random.seed(42) 

num_pontos_total = 15000 
intervalo_amostras_min = 5

data_simulada = []
timestamps_base = pd.to_datetime('2025-01-01 00:00:00')

for i in range(num_pontos_total):
    timestamp = timestamps_base + datetime.timedelta(minutes=i * intervalo_amostras_min)

    # Condições para simular alagamento (com chance de ocorrer)
    is_flood_condition = np.random.rand() < 0.15

    if is_flood_condition:
        umidade = np.random.uniform(80, 100) # Faixa alta, com sobreposição
        temperatura = np.random.uniform(10, 20) # Faixa baixa, com sobreposição
        potenciometro = 1 if np.random.rand() < 0.9 else 0 
    else:
        umidade = np.random.uniform(50, 85) # Faixa normal, com sobreposição
        temperatura = np.random.uniform(20, 30) # Faixa normal
        potenciometro = 0 if np.random.rand() < 0.95 else 1 # Apenas 5% de verdadeiros/positivos
    data_simulada.append([timestamp, umidade, temperatura, potenciometro])

df = pd.DataFrame(data_simulada, columns=['timestamp', 'umidade', 'temperatura', 'potenciometro'])
df = df.sort_values('timestamp').reset_index(drop=True)

# Engenharia de Features: Adicionar Taxa de Mudança

# Calcular a diferença da umidade e temperatura em relação ao ponto anterior
# O 'shift(1)' pega o valor da linha anterior
df['delta_umidade'] = df['umidade'].diff().fillna(0) # .fillna(0) para o primeiro ponto
df['delta_temperatura'] = df['temperatura'].diff().fillna(0)

print("Primeiras 5 linhas do DataFrame simulado (com Deltas):")
print(df.head())
print("\nContagem de classes (0=não alagamento, 1=alagamento):")
print(df['potenciometro'].value_counts())

# Preparação dos Dados para Treino

# Agora as features incluem os deltas (que adicionam maior variabilidade ao modelo)
X = df[['umidade', 'temperatura', 'delta_umidade', 'delta_temperatura']]
y = df['potenciometro']

# Teste size tb dimuido para 20%
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=None, stratify=y)


print(f"\nTamanho do conjunto de treino: {len(X_train)}")
print(f"Tamanho do conjunto de teste: {len(X_test)}")

# Treinamento da Árvore de Decisão (original) 

print("\n--- Treinando Árvore de Decisão (com dados mais complexos e deltas) ---")
model_dt = DecisionTreeClassifier(random_state=42, max_depth=8, class_weight='balanced') # class_weight ela serve para impedir o modelo de aprender apenas prever a classe majoritária (ou seja, não alagado ;v)
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

# Treinamento e Ajuste de Hiperparâmetros do Random Forest

print("\n Otimizando Random Forest com GridSearchCV ")

# Configurações do forest
param_grid = {
    'n_estimators': [50, 100, 150], # Número de árvores
    'max_depth': [5, 8, 12],       # Profundidade máxima de cada árvore
    'min_samples_leaf': [1, 2, 4], # Mínimo de amostras em uma folha
    'class_weight': ['balanced', None] # Balanceamento de classes
}

# Forest
rf_model = RandomForestClassifier(random_state=42) # Mantive random_state aqui para reprodutibilidade do RF interno

# Configura o GridSearchCV
grid_search = GridSearchCV(estimator=rf_model, param_grid=param_grid,
                           cv=3, scoring='recall', verbose=1, n_jobs=-1)

# Executa a busca pelos melhores parâmetros
grid_search.fit(X_train, y_train)

print(f"\nMelhores parâmetros encontrados: {grid_search.best_params_}")
print(f"Melhor Recall score (CV): {grid_search.best_score_:.4f}")

# Vou escolher qual modelo teve o melhor resultado e dele que irei gerar novos
best_rf_model = grid_search.best_estimator_

# Avalia o melhor forest
y_pred_best_rf = best_rf_model.predict(X_test)

print("\n Avaliação do MELHOR Random Forest ")
acuracia_best_rf = accuracy_score(y_test, y_pred_best_rf)
recall_best_rf = recall_score(y_test, y_pred_best_rf)
f1_best_rf = f1_score(y_test, y_pred_best_rf)

print(f"Acurácia (Melhor RF): {acuracia_best_rf:.4f}")
print(f"Recall (Melhor RF): {recall_best_rf:.4f}")
print(f"F1-score (Melhor RF): {f1_best_rf:.4f}")

print("\nRelatório de Classificação (Melhor RF):\n", classification_report(y_test, y_pred_best_rf))
print("\nMatriz de Confusão (Melhor RF):\n", confusion_matrix(y_test, y_pred_best_rf))


# Testando novas previsões com o MELHOR Random Forest 
print("\n Testando novas previsões com o MELHOR Random Forest ")

# Para testar, precisamos simular os deltas para as novas entradas
def predict_with_deltas(model, umidade_atual, temperatura_atual, umidade_anterior, temperatura_anterior):
    delta_u = umidade_atual - umidade_anterior
    delta_t = temperatura_atual - temperatura_anterior
    # É importante que a ordem das features seja a mesma do treinamento:
    # 'umidade', 'temperatura', 'delta_umidade', 'delta_temperatura'
    return model.predict(np.array([[umidade_atual, temperatura_atual, delta_u, delta_t]]))[0]

# Cenário 1: Normal (umidade normal, temp normal, sem grandes mudanças)
umidade_teste_1_atu = 70
temperatura_teste_1_atu = 25
umidade_teste_1_ant = 69
temperatura_teste_1_ant = 26
previsao_1_rf = predict_with_deltas(best_rf_model, umidade_teste_1_atu, temperatura_teste_1_atu, umidade_teste_1_ant, temperatura_teste_1_ant)
print(f"U: {umidade_teste_1_atu}%, T: {temperatura_teste_1_atu}°C (Delta U: {umidade_teste_1_atu - umidade_teste_1_ant:.1f}, Delta T: {temperatura_teste_1_atu - temperatura_teste_1_ant:.1f}) -> Previsão: {'Alagamento' if previsao_1_rf == 1 else 'Não Alagamento'}")

# Cenário 2: Potencial alagamento (alta umidade, baixa temperatura, queda rápida)
umidade_teste_2_atu = 95
temperatura_teste_2_atu = 18
umidade_teste_2_ant = 80 # Subiu bastante
temperatura_teste_2_ant = 25 # Caiu bastante
previsao_2_rf = predict_with_deltas(best_rf_model, umidade_teste_2_atu, temperatura_teste_2_atu, umidade_teste_2_ant, temperatura_teste_2_ant)
print(f"U: {umidade_teste_2_atu}%, T: {temperatura_teste_2_atu}°C (Delta U: {umidade_teste_2_atu - umidade_teste_2_ant:.1f}, Delta T: {temperatura_teste_2_atu - temperatura_teste_2_ant:.1f}) -> Previsão: {'Alagamento' if previsao_2_rf == 1 else 'Não Alagamento'}")

# Cenário 3: Caso de sobreposição (umidade mediana, temp mediana, mas com grandes mudanças)
umidade_teste_3_atu = 80 # Na zona de sobreposição
temperatura_teste_3_atu = 21 # Na zona de sobreposição
umidade_teste_3_ant = 70 # Subiu
temperatura_teste_3_ant = 24 # Caiu
previsao_3_rf = predict_with_deltas(best_rf_model, umidade_teste_3_atu, temperatura_teste_3_atu, umidade_teste_3_ant, temperatura_teste_3_ant)
print(f"U: {umidade_teste_3_atu}%, T: {temperatura_teste_3_atu}°C (Delta U: {umidade_teste_3_atu - umidade_teste_3_ant:.1f}, Delta T: {temperatura_teste_3_atu - temperatura_teste_3_ant:.1f}) -> Previsão: {'Alagamento' if previsao_3_rf == 1 else 'Não Alagamento'}")

plt.figure(figsize=(25, 12))
plot_tree(model_dt, feature_names=X.columns, class_names=['Não Alagamento', 'Alagamento'], filled=True, rounded=True, fontsize=8)
plt.title("Árvore de Decisão para Detecção de Alagamentos (Dados Simulados com Ruído)")
plt.show() # MOSTRA OS RESULTADOS

# Plotar Forest 
plt.figure(figsize=(25, 12))
# Pega a primeira árvore do Random Forest 
plot_tree(best_rf_model.estimators_[0],
          feature_names=X.columns,
          class_names=['Não Alagamento', 'Alagamento'],
          filled=True, rounded=True, fontsize=8)
plt.title("Uma Árvore de Decisão do Random Forest (para exemplo)")
plt.show()

# Salvar o Melhor Modelo Random Forest 
# Define o nome do arquivo onde o modelo será salvo
# O timestamp no nome garante um arquivo único a cada execução

modelo_semiperfeito = f'modelo_random_forest_alagamento_{int(time.time())}.joblib'
joblib.dump(best_rf_model, modelo_semiperfeito) 
print(f"\nModelo salvo com sucesso em '{modelo_semiperfeito}'")