# Decidi tentar o random forest e a arvore e descobrir qual se sai melhor
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.ensemble import RandomForestClassifier 
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, recall_score, f1_score
import matplotlib.pyplot as plt
import datetime

# Simulação de Dados Mais Realistas e MUUUUUITOS Casos 

np.random.seed(42)


num_pontos_total = 10000 # Vamos com 10.000 pontos agora >:)

# Gera dados de não alagamento
num_nao_alagamento = int(num_pontos_total * 0.85) 
data_nao_alagamento = []
for i in range(num_nao_alagamento):
    timestamp = datetime.datetime.now() - datetime.timedelta(minutes=np.random.randint(0, 10000))
    # Colocando ruído faz com que a arvore lide com situações mais próximas da realidade
    umidade = np.random.uniform(55, 90) # Umidade
    temperatura = np.random.uniform(18, 28) # Temperatura
    potenciometro = 0
    data_nao_alagamento.append([timestamp, umidade, temperatura, potenciometro])

# Gera dados de alagamento
num_alagamento = num_pontos_total - num_nao_alagamento
data_alagamento = []
for i in range(num_alagamento):
    timestamp = datetime.datetime.now() - datetime.timedelta(minutes=np.random.randint(0, 10000))
    umidade = np.random.uniform(75, 100) # Começa mais cedo, sobrepõe com não alagamento
    temperatura = np.random.uniform(12, 22) # Faixa mais baixa, sobrepõe com não alagamento
    potenciometro = 1
    data_alagamento.append([timestamp, umidade, temperatura, potenciometro])

# Combinar os dados e embaralhar
df = pd.DataFrame(data_nao_alagamento + data_alagamento, columns=['timestamp', 'umidade', 'temperatura', 'potenciometro'])
df = df.sample(frac=1).reset_index(drop=True) # Embaralhar para misturar alagamento/não alagamento

print("Primeiras 5 linhas do DataFrame simulado (com sobreposição):")
print(df.head())
print("\nContagem de classes (0=não alagamento, 1=alagamento):")
print(df['potenciometro'].value_counts())

# Preparação dos Dados para Treino 

X = df[['umidade', 'temperatura']] # Features
y = df['potenciometro'] # Variável Alvo

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

print(f"\nTamanho do conjunto de treino: {len(X_train)}")
print(f"Tamanho do conjunto de teste: {len(X_test)}")

# Treinamento da Árvore de Decisão (primeiro modelo)

print("\n Treinando Árvore de Decisão (com dados mais complexos) ")
model_dt = DecisionTreeClassifier(random_state=42, max_depth=8) # Aumentei um pouco a profundidade
model_dt.fit(X_train, y_train)

# Avaliação do Modelo de Árvore de Decisão
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

# Visualização da Árvore (ainda útil para entender a lógica)
plt.figure(figsize=(25, 12)) # Ajustei o tamanho para árvores maiores
plot_tree(model_dt, feature_names=X.columns, class_names=['Não Alagamento', 'Alagamento'], filled=True, rounded=True, fontsize=8)
plt.title("Árvore de Decisão para Detecção de Alagamentos (Dados Simulados com Ruído)")
plt.show()


# Tentar Outro Modelo: Random Forest (Se a Árvore de Decisão ainda for fraca)

print("\n Treinando Random Forest (afugir de overfitting) ")
# Pensei em usar o forest pelo fato dele ter menos chance de overfittar
model_rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=8) # 100 árvores de começo
model_rf.fit(X_train, y_train)

# Avaliação do Modelo Random Forest
y_pred_rf = model_rf.predict(X_test)

print("\n Avaliação do Random Forest ")
acuracia_rf = accuracy_score(y_test, y_pred_rf)
recall_rf = recall_score(y_test, y_pred_rf)
f1_rf = f1_score(y_test, y_pred_rf)

print(f"Acurácia (Random Forest): {acuracia_rf:.4f}")
print(f"Recall (Random Forest): {recall_rf:.4f}")
print(f"F1-score (Random Forest): {f1_rf:.4f}")

print("\nRelatório de Classificação (Random Forest):\n", classification_report(y_test, y_pred_rf))
print("\nMatriz de Confusão (Random Forest):\n", confusion_matrix(y_test, y_pred_rf))

# Como o modelo Random Forest pode prever um novo cenário 
print("\n Testando novas previsões com Random Forest (exemplo) ")

# Cenário 1: Normal
umidade_teste_1 = 70
temperatura_teste_1 = 25
previsao_1_rf = model_rf.predict([[umidade_teste_1, temperatura_teste_1]])
print(f"Umidade: {umidade_teste_1}%, Temperatura: {temperatura_teste_1}°C -> Previsão (RF): {'Alagamento' if previsao_1_rf[0] == 1 else 'Não Alagamento'}")

# Cenário 2: Potencial alagamento (alta umidade, baixa temperatura)
umidade_teste_2 = 95
temperatura_teste_2 = 18
previsao_2_rf = model_rf.predict([[umidade_teste_2, temperatura_teste_2]])
print(f"Umidade: {umidade_teste_2}%, Temperatura: {temperatura_teste_2}°C -> Previsão (RF): {'Alagamento' if previsao_2_rf[0] == 1 else 'Não Alagamento'}")

# Cenário 3: Caso de sobreposição (ex: umidade mediana, temperatura mediana)
umidade_teste_3 = 80 # Está na zona de sobreposição
temperatura_teste_3 = 21 # Está na zona de sobreposição
previsao_3_rf = model_rf.predict([[umidade_teste_3, temperatura_teste_3]])
print(f"Umidade: {umidade_teste_3}%, Temperatura: {temperatura_teste_3}°C -> Previsão (RF): {'Alagamento' if previsao_3_rf[0] == 1 else 'Não Alagamento'}")

modelo_beta = f'modelo_random_forest_alagamento_{int(time.time())}.joblib' # BRUTAAAAAAL ACABOOOOOU PRO BEEEEETAAAAAAA!!!!!!!!!!!!
joblib.dump(best_rf_model, modelo_beta) 
print(f"\nModelo salvo com sucesso em '{modelo_beta}'")