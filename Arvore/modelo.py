import requests
import json
import joblib 
import numpy as np 
import datetime
import time
import os 

# --- Configuração da API ---
API_URL = "https://bota.alagamentos.openlok.dev/sensor/atualizar" # URL CORRIGIDA!

# --- Carregar o Modelo de IA ---
# Certifique-se de que o caminho para o seu modelo .joblib está correto!
NOME_ARQUIVO_MODELO = 'modelo_random_forest_alagamento_1749511348.joblib' # <--- SUBSTITUA PELO SEU ARQUIVO MAIS RECENTE

loaded_model = None
if os.path.exists(NOME_ARQUIVO_MODELO):
    loaded_model = joblib.load(NOME_ARQUIVO_MODELO)
    print(f"Modelo de IA '{NOME_ARQUIVO_MODELO}' carregado com sucesso!")
else:
    print(f"ERRO: O arquivo do modelo '{NOME_ARQUIVO_MODELO}' NÃO foi encontrado.")
    print("Certifique-se de que o modelo foi salvo e o caminho/nome do arquivo está correto.")
    print("Não será possível fazer previsões de IA sem o modelo.")
    exit() 

# --- Função para Enviar Dados do Sensor e Previsão da IA ---
def enviar_dados_sensor_e_ia(umidade_atual, temperatura_atual, agua_sensor_atual, 
                            umidade_anterior, temperatura_anterior, ia_model):
    """
    Coleta, processa com a IA e envia dados de sensores + previsão de alagamento para a API.
    """
    
    # 1. Calcular os deltas (taxa de mudança)
    delta_umidade = umidade_atual - umidade_anterior
    delta_temperatura = temperatura_atual - temperatura_anterior

    # 2. Preparar as features para a IA
    # A ordem das features deve ser a mesma usada no treinamento do modelo:
    # 'umidade', 'temperatura', 'delta_umidade', 'delta_temperatura', 'agua_sensor'
    features_para_ia = np.array([[umidade_atual, temperatura_atual, 
                                  delta_umidade, delta_temperatura, agua_sensor_atual]])

    # 3. Fazer a previsão de alagamento com a IA
    previsao_alagamento_ia = ia_model.predict(features_para_ia)[0]

    # 4. Preparar o payload para a API (dados dos sensores + resultado da IA)
    payload = {
        "umidade": umidade_atual,
        "temperatura": temperatura_atual,
        "agua_sensor": agua_sensor_atual,
        "delta_umidade": delta_umidade,
        "delta_temperatura": delta_temperatura,
        "previsao_alagamento_ia": int(previsao_alagamento_ia), 
        "timestamp": datetime.datetime.now().isoformat()
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"\nEnviando dados para {API_URL}: {json.dumps(payload)}")

    try:
        response = requests.post(API_URL, data=json.dumps(payload), headers=headers)
        response.raise_for_status()

        print(f"Status da Resposta: {response.status_code}")
        print(f"Resposta da API: {response.json()}") 

    except requests.exceptions.HTTPError as errh:
        print(f"Erro HTTP na Requisição: {errh}")
        print(f"Corpo da Resposta do Servidor: {response.text}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Erro de Conexão: {errc}")
    except requests.exceptions.Timeout as errt:
        print(f"Timeout: {errt}")
    except requests.exceptions.RequestException as err:
        print(f"Ocorreu um erro inesperado: {err}")
    except json.JSONDecodeError:
        print(f"Resposta da API não é um JSON válido: {response.text}")

# --- Exemplo de Uso (Simulando Leituras ao Longo do Tempo) ---
if __name__ == "__main__":
    if loaded_model: 
        print("Iniciando simulação de coleta de dados e envio para a API com previsão de IA...\n")

        umidade_anterior = 70.0
        temperatura_anterior = 25.0

        print("\n--- Cenário 1: Condições Normais ---")
        umidade_atual_1 = 71.0
        temperatura_atual_1 = 24.5
        agua_sensor_atual_1 = 0
        enviar_dados_sensor_e_ia(umidade_atual_1, temperatura_atual_1, agua_sensor_atual_1,
                                umidade_anterior, temperatura_anterior, loaded_model)
        umidade_anterior = umidade_atual_1 
        temperatura_anterior = temperatura_atual_1
        time.sleep(2) 

        print("\n--- Cenário 2: Potencial Alagamento ---")
        umidade_atual_2 = 95.0
        temperatura_atual_2 = 18.0
        agua_sensor_atual_2 = 1 
        enviar_dados_sensor_e_ia(umidade_atual_2, temperatura_atual_2, agua_sensor_atual_2,
                                umidade_anterior, temperatura_anterior, loaded_model)
        umidade_anterior = umidade_atual_2
        temperatura_anterior = temperatura_atual_2
        time.sleep(2)

        print("\n--- Cenário 3: Água no Sensor, Condições Medianas ---")
        umidade_atual_3 = 80.0
        temperatura_atual_3 = 22.0
        agua_sensor_atual_3 = 1 
        enviar_dados_sensor_e_ia(umidade_atual_3, temperatura_atual_3, agua_sensor_atual_3,
                                umidade_anterior, temperatura_anterior, loaded_model)
        
        print("\nSimulação de envio de dados concluída.")
    else:
        print("\nNão foi possível iniciar a simulação pois o modelo de IA não foi carregado.")