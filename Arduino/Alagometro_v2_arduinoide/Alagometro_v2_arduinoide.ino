// Bibliotecas
#include <Adafruit_AHTX0.h>
#include <LedControl.h>

// Funções
#define USAR_SENSOR
#define USAR_SEMAFORO

// ================== NOVOS PARÂMETROS DE CONTROLE ==================
// --- NOVO: CONTROLE DE SENTIDO DA VIA ---
int sentidoDaVia = 1; // 1: S->N, L->O; 2: N->S, L->O; 3: S->N, O->L; 4: N->S, O->L

// Simulação dos dados de alagamento
bool alagamentoNorte = true;
bool alagamentoSul = false;
bool alagamentoLeste = false;
bool alagamentoOeste = false;
bool alagamentoLocal = false;

// Identifica o plano de ação do semáforo
enum PlanoDeAcao { NORMAL, REDIRECIONAR_ESQUERDA, REDIRECIONAR_DIREITA, PISTA_LIVRE, PISTA_BLOQUEADA };
PlanoDeAcao planoAtual = NORMAL;

// Estados para o ciclo de tempo (Verde, Amarelo, Vermelho)
enum EstadoCiclo { CICLO_VERDE, CICLO_AMARELO, CICLO_VERMELHO };
EstadoCiclo estadoCicloAtual = CICLO_VERDE;

// Controle de tempo para o ciclo (em milissegundos)
unsigned long tempoTrocaEstado = 0;
const long TEMPO_VERDE = 15000;
const long TEMPO_AMARELO = 5000;
const long TEMPO_VERMELHO = 20000;
// ===================================================================

// Pinos e Variáveis
Adafruit_AHTX0 aht;
const int pinoSensorAgua = A0;
int modoAtual = 10;
int id = 1;
int chovendo = 0;
float temperatura = 0.0;
float umidade = 0.0;
unsigned long tempoLeituraSensor = 0;
const long intervaloLeituraSensor = 5000;
unsigned long tempoPiscaAlerta = 0;
const long INTERVALO_PISCA = 600; 
bool alertaVisivel = true;

// Pinos: DIN, CLK, CS
LedControl semaforo_lc1 = LedControl(4, 2, 3, 1);
LedControl semaforo_lc2 = LedControl(7, 5, 6, 1);
LedControl semaforo_lc3 = LedControl(10, 8, 9, 1);

// Desenhos para a Matriz
const byte off[8] =       {0,0,0,0,0,0,0,0};
const byte all[8] =       {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
const byte arrowLeft[8] =  {0x08, 0x0C, 0x0E, 0xFF, 0xFF, 0x0E, 0x0C, 0x08};
const byte arrowRight[8] = {0x10, 0x30, 0x70, 0xFF, 0xFF, 0x70, 0x30, 0x10};
const byte alertSymbol[8] = {0xFF, 0xE7, 0x7E, 0x66, 0x24, 0x24, 0x18, 0x18};
const byte arrowUp[8] =    {0x18, 0x18, 0x18, 0x18, 0xFF, 0x7E, 0x3C, 0x18};

// Função Principal de Setup
void setup() {
  Serial.begin(9600);
  #ifdef USAR_SENSOR
    sensor_setup();
  #endif
  #ifdef USAR_SEMAFORO
    semaforo_setup();
  #endif
  tempoTrocaEstado = millis();
}

// Função Principal de Loop
void loop() {
  #ifdef USAR_SENSOR
    sensor_loop();
  #endif
  #ifdef USAR_SEMAFORO
    semaforo_loop();
  #endif
}

// Lógica dos sensores
void sensor_setup() {
  pinMode(pinoSensorAgua, INPUT);
  Serial.println("Inicializando Sensores...");
  if (!aht.begin()) {
    Serial.println("Não foi possível encontrar o AHT10!");
    while (1) delay(10);
  }
  Serial.println("Sensores prontos.");
}
void sensor_loop() {
  if (millis() - tempoLeituraSensor >= intervaloLeituraSensor) {
    tempoLeituraSensor = millis();
    sensors_event_t humidity_event, temp_event;
    aht.getEvent(&humidity_event, &temp_event);
    int leituraAgua = analogRead(pinoSensorAgua);
    chovendo = (leituraAgua > 200) ? 1 : 0;
    temperatura = temp_event.temperature;
    umidade = humidity_event.relative_humidity;
    float arrayAlagometro[4] = {id, chovendo, temperatura, umidade};
    Serial.print("Dados - Molhado: "); Serial.print(chovendo);
    Serial.print(", Umidade: "); Serial.print(umidade);
    Serial.print(", Temperatura: "); Serial.print(temperatura); Serial.println(".");
  }
}

// Lógica do semáforo
void desenharMatriz(LedControl &lc, const byte pattern[8]) {
  for (int i = 0; i < 8; i++) {
    lc.setRow(0, i, pattern[i]);
  }
}
void exibirPadraoContinuo(const byte m1[8], const byte m2[8], const byte m3[8]) {
  desenharMatriz(semaforo_lc1, m1);
  desenharMatriz(semaforo_lc2, m2);
  desenharMatriz(semaforo_lc3, m3);
}
void semaforo_setup() {
  semaforo_lc1.shutdown(0, false);
  semaforo_lc1.setIntensity(0, 8);
  semaforo_lc1.clearDisplay(0);
  semaforo_lc2.shutdown(0, false);
  semaforo_lc2.setIntensity(0, 8);
  semaforo_lc2.clearDisplay(0);
  semaforo_lc3.shutdown(0, false);
  semaforo_lc3.setIntensity(0, 8);
  semaforo_lc3.clearDisplay(0);
  Serial.println("Semáforos (3 matrizes) inicializados com lógica inteligente.");
}

// ================== LÓGICA INTELIGENTE DO SEMÁFORO (VERSÃO FINAL CORRIGIDA) ==================
void definirPlanoDeAcao() {
  // A verificação de alagamento na origem/local foi movida para semaforo_loop() como prioridade máxima.

  // PRIORIDADE 1: VERIFICA SE A VIA INTEIRA ESTÁ BLOQUEADA
  if (alagamentoNorte && alagamentoSul) {
    planoAtual = PISTA_BLOQUEADA;
    return;
  }

  // PRIORIDADE 2: ANALISA O FLUXO DA VIA PRINCIPAL E POSSÍVEIS REDIRECIONAMENTOS
  switch (sentidoDaVia) {
    case 1: // Via Principal: Sul -> Norte / Cruzamento: Leste -> Oeste
      if (alagamentoNorte) {
        if (!alagamentoOeste) { planoAtual = REDIRECIONAR_ESQUERDA; } 
        else { planoAtual = PISTA_BLOQUEADA; }
        return;
      }
      break;
    case 2: // Via Principal: Norte -> Sul / Cruzamento: Leste -> Oeste
      if (alagamentoSul) {
        if (!alagamentoOeste) { planoAtual = REDIRECIONAR_DIREITA; } 
        else { planoAtual = PISTA_BLOQUEADA; }
        return;
      }
      break;
    case 3: // Via Principal: Sul -> Norte / Cruzamento: Oeste -> Leste
      if (alagamentoNorte) {
        if (!alagamentoLeste) { planoAtual = REDIRECIONAR_DIREITA; } 
        else { planoAtual = PISTA_BLOQUEADA; }
        return;
      }
      break;
    case 4: // Via Principal: Norte -> Sul / Cruzamento: Oeste -> Leste
      if (alagamentoSul) {
        if (!alagamentoLeste) { planoAtual = REDIRECIONAR_ESQUERDA; } 
        else { planoAtual = PISTA_BLOQUEADA; }
        return;
      }
      break;
  }

  // PRIORIDADE 3: VERIFICA A VIA TRANSVERSAL
  if (alagamentoLeste && alagamentoOeste) {
    planoAtual = PISTA_LIVRE;
    return;
  }

  // PRIORIDADE 4: OPERAÇÃO NORMAL
  planoAtual = NORMAL;
}

// A função executarCicloDeTempo permanece a mesma
void executarCicloDeTempo() {
    unsigned long tempoAtual = millis();
    int casoVerde, casoAmarelo, casoVermelho;

    switch (planoAtual) {
        case NORMAL:
            casoVerde = 10; casoAmarelo = 9; casoVermelho = 8;
            break;
        case REDIRECIONAR_ESQUERDA:
            casoVerde = 6; casoAmarelo = 1; casoVermelho = 4;
            break;
        case REDIRECIONAR_DIREITA:
            casoVerde = 7; casoAmarelo = 1; casoVermelho = 3;
            break;
        case PISTA_LIVRE:
            modoAtual = 5; 
            return; 
        case PISTA_BLOQUEADA:
            modoAtual = 1; 
            return;
    }

    switch (estadoCicloAtual) {
        case CICLO_VERDE:
            modoAtual = casoVerde;
            if (tempoAtual - tempoTrocaEstado >= TEMPO_VERDE) { estadoCicloAtual = CICLO_AMARELO; tempoTrocaEstado = tempoAtual; }
            break;
        case CICLO_AMARELO:
            modoAtual = casoAmarelo;
            if (tempoAtual - tempoTrocaEstado >= TEMPO_AMARELO) { estadoCicloAtual = CICLO_VERMELHO; tempoTrocaEstado = tempoAtual; }
            break;
        case CICLO_VERMELHO:
            modoAtual = casoVermelho;
            if (tempoAtual - tempoTrocaEstado >= TEMPO_VERMELHO) { estadoCicloAtual = CICLO_VERDE; tempoTrocaEstado = tempoAtual; }
            break;
    }
}

void semaforo_loop() {
  // --- DISJUNTOR DE EMERGÊNCIA (NOVA LÓGICA DE PRIORIDADE MÁXIMA) ---
  // Se a origem do tráfego ou o ponto local estão alagados, desliga tudo e para.
  bool origemAlagada = ((sentidoDaVia == 1 || sentidoDaVia == 3) && alagamentoSul) ||
                         ((sentidoDaVia == 2 || sentidoDaVia == 4) && alagamentoNorte);

  if (alagamentoLocal || origemAlagada) {
    exibirPadraoContinuo(off, off, off); // Desliga todas as matrizes.
    return; // Sai imediatamente da função, ignorando o resto da lógica.
  }

  // --- LÓGICA NORMAL (SÓ EXECUTA SE A EMERGÊNCIA NÃO FOR ATIVADA) ---
  // LÓGICA DO PISCA-PISCA
  if (millis() - tempoPiscaAlerta >= INTERVALO_PISCA) {
    alertaVisivel = !alertaVisivel;
    tempoPiscaAlerta = millis();
  }
  const byte* simboloAlertaAtual;
  if (alertaVisivel) {
    simboloAlertaAtual = alertSymbol;
  } else {
    simboloAlertaAtual = off;
  }
  
  definirPlanoDeAcao();
  executarCicloDeTempo();

  // Desenha o modo atual
  switch (modoAtual) {
    case 0:  exibirPadraoContinuo(off, off, off); break;
    case 1:  exibirPadraoContinuo(off, simboloAlertaAtual, off); break;
    case 2:  exibirPadraoContinuo(arrowUp, simboloAlertaAtual, off); break;
    case 3:  exibirPadraoContinuo(arrowRight, simboloAlertaAtual, off); break;
    case 4:  exibirPadraoContinuo(arrowLeft, simboloAlertaAtual, off); break;
    case 5:  exibirPadraoContinuo(off, simboloAlertaAtual, arrowUp); break;
    case 6:  exibirPadraoContinuo(off, simboloAlertaAtual, arrowLeft); break;
    case 7:  exibirPadraoContinuo(off, simboloAlertaAtual, arrowRight); break;
    case 8:  exibirPadraoContinuo(all, off, off); break;
    case 9:  exibirPadraoContinuo(off, all, off); break;
    case 10: exibirPadraoContinuo(off, off, all); break;
    default: exibirPadraoContinuo(off, off, off); break;
  }
}