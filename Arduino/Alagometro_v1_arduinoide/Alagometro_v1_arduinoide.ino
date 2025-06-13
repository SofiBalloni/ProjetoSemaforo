#include <Adafruit_AHTX0.h>
#include <LedControl.h>

// ============= Configurações Gerais =============
// As diretivas abaixo mantêm o código organizado.
// Deixe-as como estão para usar tanto o sensor quanto o semáforo.
#define USAR_SENSOR
#define USAR_SEMAFORO

// ============= Variáveis de Controle e Configuração =============

// !! CONTROLE MANUAL AQUI !!
// Mude o número da variável abaixo para escolher o que o semáforo vai mostrar.
// Os modos vão de 0 a 10, conforme sua lista original.
int modoAtual = 4;

// ============= Variáveis Globais dos Sensores =============
Adafruit_AHTX0 aht;
const int pinoSensorAgua = A0;
// Variáveis para armazenar os dados dos sensores
int id = 1;
int chovendo = 0;
float temperatura = 0.0;
float umidade = 0.0;
// Controle de tempo para leitura do sensor (não-bloqueante)
unsigned long tempoLeituraSensor = 0;
const long intervaloLeituraSensor = 5000; // Ler a cada 5 segundos

// ============= Variáveis Globais do Semáforo (3 MATRIZES) =============
// Pinos: DIN, CLK, CS
LedControl semaforo_lc1 = LedControl(4, 2, 3, 1);   // Matriz 1 (Esquerda)
LedControl semaforo_lc2 = LedControl(7, 5, 6, 1);   // Matriz 2 (Centro)
LedControl semaforo_lc3 = LedControl(11, 10, 12, 1); // Matriz 3 (Direita)

// ============= Desenhos para a Matriz 8x8 =============
const byte off[8] =        {0,0,0,0,0,0,0,0};
const byte all[8] =        {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
const byte arrowLeft[8] =  {0x08, 0x0C, 0x0E, 0xFF, 0xFF, 0x0E, 0x0C, 0x08};
const byte arrowRight[8] = {0x10, 0x30, 0x70, 0xFF, 0xFF, 0x70, 0x30, 0x10};
const byte alertSymbol[8] = {0xFF, 0xE7, 0x7E, 0x66, 0x24, 0x24, 0x18, 0x18};
const byte arrowUp[8] =    {0x18, 0x18, 0x18, 0x18, 0xFF, 0x7E, 0x3C, 0x18};

// ============= Função Principal de Setup =============
void setup() {
  Serial.begin(9600);
  #ifdef USAR_SENSOR
    sensor_setup();
  #endif
  #ifdef USAR_SEMAFORO
    semaforo_setup();
  #endif
}

// ============= Função Principal de Loop =============
void loop() {
  #ifdef USAR_SENSOR
    sensor_loop();    // Lê os sensores e mostra no Serial.
  #endif
  #ifdef USAR_SEMAFORO
    semaforo_loop();  // Controla os LEDs com base no 'modoAtual'.
  #endif
}

// ===============================================
//               LÓGICA DOS SENSORES
// ===============================================
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
  // Leitura não-bloqueante a cada 5 segundos.
  if (millis() - tempoLeituraSensor >= intervaloLeituraSensor) {
    tempoLeituraSensor = millis();
    sensors_event_t humidity_event, temp_event;
    aht.getEvent(&humidity_event, &temp_event);
    int leituraAgua = analogRead(pinoSensorAgua);
    chovendo = (leituraAgua > 200) ? 1 : 0;
    temperatura = temp_event.temperature;
    umidade = humidity_event.relative_humidity;

    float arrayAlagometro[4] = {id, chovendo, temperatura, umidade};

    Serial.print("Dados -> Chovendo: "); Serial.print(chovendo ? "Sim" : "Não");
    Serial.print(", Umidade: "); Serial.print(umidade);
    Serial.print("%, Temp: "); Serial.print(temperatura); Serial.println(" *C");
  }
}

// ===============================================
//              LÓGICA DO SEMÁFORO
// ===============================================

/**
 * @brief Desenha um padrão em uma única matriz de LED.
 */
void desenharMatriz(LedControl &lc, const byte pattern[8]) {
  for (int i = 0; i < 8; i++) {
    lc.setRow(0, i, pattern[i]);
  }
}

/**
 * @brief Envia os padrões para as três matrizes de uma vez para exibição contínua.
 */
void exibirPadraoContinuo(const byte m1[8], const byte m2[8], const byte m3[8]) {
  desenharMatriz(semaforo_lc1, m1);
  desenharMatriz(semaforo_lc2, m2);
  desenharMatriz(semaforo_lc3, m3);
}

void semaforo_setup() {
  // Acorda e configura o brilho de cada matriz
  semaforo_lc1.shutdown(0, false);
  semaforo_lc1.setIntensity(0, 8);
  semaforo_lc1.clearDisplay(0);

  semaforo_lc2.shutdown(0, false);
  semaforo_lc2.setIntensity(0, 8);
  semaforo_lc2.clearDisplay(0);

  semaforo_lc3.shutdown(0, false);
  semaforo_lc3.setIntensity(0, 8);
  semaforo_lc3.clearDisplay(0);
  
  Serial.println("Semáforos (3 matrizes) inicializados em modo manual.");
}

void semaforo_loop() {
  // Esta é a sua lógica de controle manual.
  // O switch chama a função 'exibirPadraoContinuo',
  // que desenha os padrões sem delays ou limpeza,
  // garantindo uma imagem sólida e constante.
  switch (modoAtual) {
    case 0:  // Desligado
      exibirPadraoContinuo(off, off, off);
      break;
    case 1:  // Alerta no centro
      exibirPadraoContinuo(off, alertSymbol, off);
      break;
    case 2:  // Siga em frente na matriz 1, alerta na 2
      exibirPadraoContinuo(arrowUp, alertSymbol, off);
      break;
    case 3:  // Seta direita na 1, alerta na 2
      exibirPadraoContinuo(arrowRight, alertSymbol, off);
      break;
    case 4:  // Seta esquerda na 1, alerta na 2
      exibirPadraoContinuo(arrowLeft, alertSymbol, off);
      break;
    case 5:  // Alerta na 2, siga em frente na 3
      exibirPadraoContinuo(off, alertSymbol, arrowUp);
      break;
    case 6:  // Alerta na 2, seta esquerda na 3
      exibirPadraoContinuo(off, alertSymbol, arrowLeft);
      break;
    case 7:  // Alerta na 2, seta direita na 3
      exibirPadraoContinuo(off, alertSymbol, arrowRight);
      break;
    case 8:  // Vermelho (apenas matriz 1)
      exibirPadraoContinuo(all, off, off);
      break;
    case 9:  // Amarelo (apenas matriz 2)
      exibirPadraoContinuo(off, all, off);
      break;
    case 10: // Verde (apenas matriz 3)
      exibirPadraoContinuo(off, off, all);
      break;
    default: // Padrão: Desliga tudo
      exibirPadraoContinuo(off, off, off);
      break;
  }
}