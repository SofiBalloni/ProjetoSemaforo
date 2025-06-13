# Semáforo Inteligente

Um sistema de detecção e redirecionamento de tráfego durante alagamentos

# Funcionamento
``` mermaid
graph
    subgraph Zona de Risco de Alagamento
    SENSORES("Sensores de Alagamento")
    CONTR("Controlador de Tráfego")
    SEM("Semáforos Seguros")
    end

    subgraph Nuvem
    API["API de Comunicação"]
    DETC["Serviço de Detecção de Alagamentos"]
    DB[("Banco de Dados SQL")]
    WEB(["Painel de Monitoramento Online"])
    end

    SENSORES -.->|Dados do Sensor| API

    API --->|Dados de Alagamento| DETC
    API ==== DB
    DETC --->|Zonas Alagadas| API
    API --->|Zonas Alagadas| WEB

    API -.->|Zonas Alagadas| CONTR
    CONTR ===|Redirecionar| SEM
```

# Componentes

1. ## Zona de Risco de Alagamento:
- **Sensores de Alagamento:** Esses sensores detectam os níveis de água e as condições de inundação na área.
- **Controlador de Tráfego:** Este dispositivo gerencia os semáforos com base nos dados recebidos dos sensores e dos serviços em nuvem.
- **Semáforos Seguros:** São os semáforos controlados para garantir o fluxo seguro do tráfego, especialmente durante inundações.

2. ## Nuvem:
- **API de Comunicação:** Serve como interface para troca de dados entre os sensores locais e os serviços em nuvem.
- **Serviço de Detecção de Alagamentos:** Este serviço processa os dados recebidos dos sensores para identificar áreas inundadas.
- **Banco de Dados SQL:** Armazena dados relacionados a eventos de inundação, leituras de sensores e outras informações relevantes.
- **Painel de Monitoramento Online:** Este componente fornece uma interface de usuário para monitorar as condições de inundação e o gerenciamento do tráfego em tempo real. Ele exibe os dados recebidos da API, incluindo alertas sobre zonas alagadas e status dos semáforos.

# Interações

1. **Fluxo de Dados dos Sensores para a API:**
Os sensores de inundação enviam dados para a API de Comunicação, indicados pela linha tracejada (que geralmente representa uma conexão menos direta ou assíncrona).

1. **Processamento de Dados:**
O Serviço de Detecção de Inundações busca os dados dos sensores utilizando a API, analisando as informações para determinar se há áreas inundadas.

1. **Resultados da Detecção de Inundações:**
O Serviço de Detecção de Inundações envia informações sobre zonas inundadas de volta para a API.

1. **Interação com o Banco de Dados:**
A API tem uma conexão direta com o Banco de Dados SQL, para armazenar dados dos sensores e resultados da detecção de inundações.

1. **Resposta do Controle de Tráfego:**
O Controlador de Tráfego periodicamente busca zonas inundadas na API, utilizando essas informações para gerenciar os semáforos adequadamente.
O Controlador de Tráfego envia comandos aos Semáforos Seguros para redirecionar o tráfego para longe das áreas inundadas.

1. **Fluxo de Dados para o Painel de Monitoramento:** O Painel de Monitoramento Online busca informações de zonas alagadas utilizando a API, permitindo que os usuários visualizem as condições atuais e tomem decisões informadas.
