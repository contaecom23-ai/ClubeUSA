from slowapi import Limiter
from slowapi.util import get_remote_address

# Instância única compartilhada por todos os routers.
# Ter múltiplas instâncias seria errado: cada uma tem seu próprio storage
# e os contadores não convergem para o mesmo limite global.
limiter = Limiter(key_func=get_remote_address)
