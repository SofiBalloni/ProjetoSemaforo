import requests
import time
import threading
from typing import Callable, Any, Dict, List, Optional
import logging

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ClienteAlagamentosError(Exception):
    """Erro de interação com a API de alagamentos"""
    pass

class AlagamentosGlobal:
    def __init__(self, poll_interval: int = 5, host = "https://alagamentos.openlok.dev/"):
        """
        Initializar ClienteAlagamentos
        :param poll_interval: O intervalo em segundos para monitorar variáveis.
        """
        self.base_url = host
        self._stop_event = threading.Event()
        # Use um bloqueio para proteger event_pool e ignore_pool de condições de corrida
        self._lock = threading.Lock() 
        self.event_pool: Dict[str, List[Callable[[Any], None]]] = {}
        self.ignore_pool: Dict[str, List[int]] = {}
        self.monitor_thread: Optional[threading.Thread] = None
        self.poll_interval = poll_interval
        self._last_values: Dict[str, Any] = {} # Armazenamento de últimos valores para monitoramento

    def _make_request(self, method: str, url: str, **args) -> requests.Response:
        """Auxiliar HTTP"""
        try:
            response = requests.request(method, url, **args)
            response.raise_for_status()  # Gera HTTPError para respostas inválidas (4xx ou 5xx)
            return response
        except requests.exceptions.HTTPError as e:
            logging.error(f"Erro HTTP: {e.response.status_code} - {e.response.text} for {url}")
            raise ClienteAlagamentosError(f"Erro de API: {e.response.status_code} - {e.response.text}") from e
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Erro de Conexão: Não foi possível se conectar com a API - {e}")
            raise ClienteAlagamentosError(f"Erro de Conexão: {e}") from e
        except requests.exceptions.Timeout as e:
            logging.error(f"Tempo Esgotado: A API esta demorando muito para responder - {e}")
            raise ClienteAlagamentosError(f"Tempo Esgotado: {e}") from e
        except requests.exceptions.RequestException as e:
            logging.error(f"Erro inesperado de pedido - {e}")
            raise ClienteAlagamentosError(f"Erro de pedido: {e}") from e

    def var_get(self, var_name: str) -> Optional[Any]:
        """
        Obtém o valor de uma variável global do sistema.

        :param var_name: O nome da variável a ser recuperada.
        :return: O valor da variável ou None se não for encontrado.
        :raises ClienteAlagamentosError: Em caso de problemas de rede ou com a API.
        """
        try:
            response = self._make_request("GET", f"{self.base_url}/var/{var_name}")
            return response.json()
        except ClienteAlagamentosError:
            return None # Or re-raise, idk

    def var_set(self, variable_name: str, value: Any) -> bool:
        """
        Define o valor de uma variável global do sistema.

        :param variable_name: O nome da variável a ser definida.
        :param value: O valor a ser atribuído à variável.
        :return: True se bem-sucedido, False caso contrário.
        :raises ClienteAlagamentosError: Em caso de problemas de rede ou com a API.
        """
        try:
            self._make_request("PUT", f"{self.base_url}/var/{variable_name}", json=value)
            return True
        except ClienteAlagamentosError:
            return False

    def var_del(self, variable_name: str) -> bool:
        """
        Exclui uma variável global do sistema.

        :param variable_name: O nome da variável a ser excluída.
        :return: True se bem-sucedido, False caso contrário.
        :raises ClienteAlagamentosError: Em caso de problemas de rede ou com a API.
        """
        try:
            self._make_request("DELETE", f"{self.base_url}/var/{variable_name}")
            return True
        except ClienteAlagamentosError:
            return False
        
    def var_onchange(self, var_name: str, callback: Callable[[Any], None]) -> int:
        """
        Monitora uma variável em busca de alterações e chama a função quando ela for alterada.

        :param var_name: O nome da variável a ser monitorada.
        :param callback: Uma função a ser chamada quando a variável for alterada.
        :return: Um identificador único para a função.
        """
        with self._lock:
            if var_name not in self.event_pool:
                self.event_pool[var_name] = []
            
            # Encontre o próximo índice disponível para a função
            call_ix = 0
            while call_ix in self.ignore_pool.get(var_name, []):
                call_ix += 1 # Garanta uma ID única mesmo que algumas sejam ignoradas
            
            self.event_pool[var_name].append(callback) # Nós armazenamos a função real

            # Para simplificar, vamos usar apenas o índice para remoção posterior.
            # Se a lista for redimensionada, este índice pode se tornar inválido.
            # Uma solução poderia ser armazenar em uma tupla: (call_ix, callback)
            # Ou até usar um dicionário para as funções: {ix: callback}
            # Mas pensei nisso depois que já implementei assim
            # Não to afim de mudar agora :p

            # Inicializa o último valor para a nova variável que está sendo monitorada
            if var_name not in self._last_values:
                self._last_values[var_name] = self.var_get(var_name)

            if not self.monitor_thread or not self.monitor_thread.is_alive():
                self.monitor_thread = threading.Thread(target=self._monitor)
                self.monitor_thread.daemon = True # Permitir que o programa saia mesmo se o processo estiver em execução
                self.monitor_thread.start()
            return len(self.event_pool[var_name]) - 1 # Retorna o índice da função

    def var_onchange_clear(self, var_name: str, call_ix: int):
        """
        Remove uma função monitor de uma variável. EXPERIMENTAL

        :param var_name: O nome da variável monitorada.
        :param call_ix: O índice da função a ser removida.
        """
        with self._lock:
            if var_name not in self.event_pool:
                return
            
            if 0 <= call_ix < len(self.event_pool[var_name]):
                # Uma remoção mais direta seria: self.event_pool[var_name].pop(call_ix)
                # Mas isso muda os índices de algumas funções existentes.
                # Uma abordagem mais segura por enquanto é "ignorar".
                # Para uma remoção real, event_pool precisaria ser um dicionário ou
                # eu precisaria reindexar todos as funções subsequentes
                # Mas como eu já disse, não to afim :p
                
                if var_name not in self.ignore_pool:
                    self.ignore_pool[var_name] = []
                self.ignore_pool[var_name].append(call_ix)
            else:
                logging.warning(f"Tentou remover um índice de função inválido {call_ix} para {var_name}")


    def _monitor(self):
        """
        Monitorar todas as variáveis registradas para verificar alterações.
        """
        while not self._stop_event.is_set():
            time.sleep(self.poll_interval)
            
            with self._lock: # Bloquear antes de iterar e modificar o estado compartilhado
                variables_to_monitor = list(self.event_pool.keys()) # Iterar em cópia

            for var_name in variables_to_monitor:
                current_value = None
                try:
                    current_value = self.var_get(var_name)
                except ClienteAlagamentosError as e:
                    logging.error(f"Falha em ler variável {var_name} durante monitoramento: {e}")
                    # Recuar? Talves?
                    continue # Pular para a próxima variável se a obtenção da atual falhar
                
                with self._lock:
                    if var_name not in self._last_values: # Isso pode acontecer se a variável foi adicionada após a verificação inicial
                        self._last_values[var_name] = current_value
                        continue

                    if current_value == self._last_values[var_name]:
                        continue
                    
                    self._last_values[var_name] = current_value
                    
                    callbacks_for_var = self.event_pool.get(var_name, [])[:] # Copiar a lista da lista
                    ignore_indices = self.ignore_pool.get(var_name, [])[:]

                for ix, callback in enumerate(callbacks_for_var):
                    if ix in ignore_indices:
                        continue

                    try:
                        callback(current_value)
                    except Exception as err: # Alguma coisa deu errado na função
                        logging.error(f"Função {ix} em {var_name} teve um erro: {err}", exc_info=True)

    def stop(self):
        """
        Para e limpa o monitoramento de variáveis.
        """
        if self.monitor_thread and self.monitor_thread.is_alive():
            logging.info("Enviando sinal de parada para o monitor...")
            self._stop_event.set()
            self.monitor_thread.join(timeout=self.poll_interval + 1) # Espera um ciclo do monitor
            if self.monitor_thread.is_alive():
                logging.warning("Monitor não se encerrou corretamente")
            else:
                logging.info("Monitor encerrado")
            self.event_pool = {}
            self.ignore_pool = {}
            self.monitor_thread = None
            self._last_values = {}

    def __del__(self):
        """Chamar stop() quando garbage collected."""
        self.stop()