"""Catálogo curado de comandos Linux + Git, em PT-BR (offline).

Herda a ideia do catálogo `comandos`/`linux` do chronos e estende pra git.
Escopo: o essencial pra quem está no Mês 1 (Linux+Git). Cada comando tem
descrição, uso, exemplos e (às vezes) uma dica. `tool` separa linux de git.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Command:
    name: str
    tool: str  # "linux" | "git"
    cat: str
    desc: str
    usage: str
    examples: list[str] = field(default_factory=list)
    tip: str = ""


COMMANDS: list[Command] = [
    # ---------------- LINUX: navegação ----------------
    Command("pwd", "linux", "navegação", "mostra o diretório atual (onde você está)", "pwd"),
    Command("ls", "linux", "navegação", "lista arquivos e pastas", "ls [opções] [caminho]",
            ["ls -la  → mostra ocultos + detalhes", "ls -lh  → tamanhos legíveis (KB/MB)"],
            "arquivos que começam com . são ocultos; só aparecem com -a."),
    Command("cd", "linux", "navegação", "entra em um diretório", "cd <caminho>",
            ["cd ~   → vai pra sua home", "cd ..  → sobe um nível", "cd -   → volta ao anterior"]),
    Command("tree", "linux", "navegação", "mostra a árvore de diretórios", "tree [caminho]",
            ["tree -L 2  → só 2 níveis de profundidade"]),

    # ---------------- LINUX: arquivos ----------------
    Command("mkdir", "linux", "arquivos", "cria diretório", "mkdir [-p] <nome>",
            ["mkdir -p a/b/c  → cria a cadeia toda de uma vez"]),
    Command("touch", "linux", "arquivos", "cria arquivo vazio (ou atualiza data)", "touch <arquivo>"),
    Command("cp", "linux", "arquivos", "copia arquivos/pastas", "cp [-r] origem destino",
            ["cp -r pasta/ backup/  → copia pasta inteira (-r = recursivo)"]),
    Command("mv", "linux", "arquivos", "move OU renomeia", "mv origem destino",
            ["mv velho.txt novo.txt  → renomeia", "mv arq.txt ~/docs/  → move"]),
    Command("rm", "linux", "arquivos", "apaga arquivos/pastas (SEM lixeira!)", "rm [-rf] <alvo>",
            ["rm arquivo.txt", "rm -r pasta/  → apaga pasta e conteúdo"],
            "CUIDADO: rm -rf não pergunta e não tem desfazer."),
    Command("find", "linux", "arquivos", "procura arquivos por nome/tipo/data", "find <caminho> -name <padrão>",
            ["find . -name '*.py'  → todos os .py a partir daqui",
             "find /var -size +100M  → arquivos maiores que 100MB"]),
    Command("ln", "linux", "arquivos", "cria link (atalho) para um arquivo", "ln -s alvo link",
            ["ln -s /opt/app/bin app  → link simbólico chamado 'app'"]),

    # ---------------- LINUX: ver conteúdo ----------------
    Command("cat", "linux", "conteúdo", "mostra o conteúdo do arquivo inteiro", "cat <arquivo>",
            ["cat -n arq  → com número de linha"]),
    Command("less", "linux", "conteúdo", "abre arquivo pra rolar (q pra sair)", "less <arquivo>",
            [], "dentro do less: / pesquisa, q sai, espaço avança página."),
    Command("head", "linux", "conteúdo", "mostra as primeiras linhas", "head [-n N] <arquivo>",
            ["head -n 20 log.txt  → primeiras 20 linhas"]),
    Command("tail", "linux", "conteúdo", "mostra as últimas linhas", "tail [-n N] [-f] <arquivo>",
            ["tail -f app.log  → acompanha o log AO VIVO (Ctrl+C sai)"],
            "tail -f é o jeito clássico de assistir um log crescer."),
    Command("nano", "linux", "conteúdo", "editor de texto simples no terminal", "nano <arquivo>",
            [], "Ctrl+O salva, Ctrl+X sai."),

    # ---------------- LINUX: texto/busca ----------------
    Command("grep", "linux", "texto", "procura um padrão dentro de texto/arquivos", "grep [opções] <padrão> <arquivo>",
            ["grep -i erro log.txt  → ignora maiúsc/minúsc",
             "grep -rn TODO .  → recursivo, com nº da linha",
             "ps aux | grep nginx  → filtra a saída de outro comando"]),
    Command("sed", "linux", "texto", "edita texto em fluxo (substituir, apagar)", "sed 's/velho/novo/g' <arquivo>",
            ["sed -i 's/foo/bar/g' arq  → substitui no próprio arquivo (-i)"]),
    Command("awk", "linux", "texto", "processa colunas de texto", "awk '{print $N}'",
            ["ps aux | awk '{print $2, $11}'  → mostra PID e comando"]),
    Command("wc", "linux", "texto", "conta linhas, palavras, bytes", "wc [-l] <arquivo>",
            ["wc -l arq  → só o número de linhas"]),
    Command("sort", "linux", "texto", "ordena linhas", "sort [-n] <arquivo>",
            ["sort -n  → ordem numérica"]),
    Command("uniq", "linux", "texto", "remove linhas duplicadas ADJACENTES", "uniq [-c]",
            ["sort arq | uniq -c  → conta ocorrências (ordene antes!)"]),

    # ---------------- LINUX: processos ----------------
    Command("ps", "linux", "processos", "lista processos", "ps aux",
            ["ps aux | grep python  → acha processos do python"]),
    Command("top", "linux", "processos", "monitor de processos ao vivo (q sai)", "top"),
    Command("htop", "linux", "processos", "top melhorado, colorido e interativo", "htop"),
    Command("kill", "linux", "processos", "envia sinal (encerra) a um processo", "kill [-9] <PID>",
            ["kill 1234", "kill -9 1234  → força (último recurso)"]),
    Command("jobs", "linux", "processos", "lista tarefas em segundo plano do shell", "jobs"),

    # ---------------- LINUX: sistema ----------------
    Command("df", "linux", "sistema", "espaço em disco por partição", "df -h",
            ["df -h  → tamanhos legíveis"]),
    Command("du", "linux", "sistema", "espaço usado por pastas/arquivos", "du -sh <caminho>",
            ["du -sh *  → tamanho de cada item da pasta atual"]),
    Command("free", "linux", "sistema", "uso de memória RAM", "free -h"),
    Command("uname", "linux", "sistema", "informações do kernel/SO", "uname -a"),
    Command("uptime", "linux", "sistema", "há quanto tempo ligado + load average", "uptime"),
    Command("systemctl", "linux", "sistema", "controla serviços (systemd)", "systemctl <ação> <serviço>",
            ["sudo systemctl status nginx  → vê se está rodando (q sai)",
             "sudo systemctl start nginx  → liga o serviço agora",
             "sudo systemctl enable nginx  → inicia junto com o sistema",
             "sudo systemctl restart nginx  → reinicia"],
            "status é leitura; start/stop/restart/enable mexem no serviço (precisa sudo)."),

    # ---------------- LINUX: rede ----------------
    Command("ping", "linux", "rede", "testa se uma máquina responde (ICMP)", "ping [-c N] <host>",
            ["ping -c 3 google.com  → envia 3 pacotes e para"],
            "dica: veja isso ao vivo com 'thorn explain ping <host>'."),
    Command("traceroute", "linux", "rede", "mostra os saltos (roteadores) até o destino", "traceroute <host>",
            ["traceroute google.com",
             "sudo traceroute -I google.com  → via ICMP, fura NAT que bloqueia UDP"],
            "no lab (NAT do VirtualBox) muitos saltos viram *; use 'thorn explain traceroute'."),
    Command("tcpdump", "linux", "rede", "espiona os pacotes crus na rede (o raio-x)", "sudo tcpdump -n -i any [filtro]",
            ["sudo tcpdump -n -i any tcp port 80", "sudo tcpdump -n -i any icmp",
             "filtros: icmp · tcp port 80 · udp port 53 · host google.com"],
            "-n não traduz nomes · -i any todas as interfaces · Ctrl+C para. Veja 'thorn explain tcpdump'."),
    Command("ip", "linux", "rede", "mostra/config interfaces e rotas", "ip <objeto>",
            ["ip -br a  → seus IPs e interfaces (resumido)", "ip r  → tabela de rotas (mostra o gateway)"],
            "cuidado: é 'ip r' (sem hífen); e '-br' vem ANTES do objeto (ip -br a)."),
    Command("ipcalc", "linux", "rede", "calcula rede/broadcast/hosts de um CIDR", "ipcalc <ip>/<máscara>",
            ["ipcalc 10.0.2.15/24  → rede, broadcast e faixa de hosts"]),
    Command("ss", "linux", "rede", "mostra portas/conexões e quem escuta (substitui netstat)", "ss -tlnp",
            ["sudo ss -tlnp  → portas TCP em escuta + o processo",
             "ss -tulpn  → inclui UDP também"],
            "flags: t=TCP · u=UDP · l=listening · n=números · p=processo."),
    Command("curl", "linux", "rede", "faz requisições HTTP na linha de comando", "curl [opções] <url>",
            ["curl -v https://site  → verboso: DNS/TCP/TLS/HTTP",
             "curl -I https://google.com  → só os cabeçalhos",
             "curl -IL https://google.com  → segue redirects (301/302)",
             "curl -X POST -d 'n=savio' https://postman-echo.com/post  → envia dados",
             "curl ifconfig.me  → seu IP público (vê o NAT)"],
            "atalho: 'thorn explain curl <url>' mostra cada camada com dado real."),
    Command("wget", "linux", "rede", "baixa arquivos da web", "wget <url>",
            ["wget -O nome.zip url  → salva com esse nome"]),
    Command("dig", "linux", "rede", "consulta DNS (resolução de nomes)", "dig [@servidor] [TIPO] <domínio>",
            ["dig +short google.com  → só o IP",
             "dig MX gmail.com  → registro específico (A, MX, TXT, NS, AAAA)",
             "dig +trace google.com  → hierarquia raiz → .com → domínio",
             "dig @8.8.8.8 google.com  → pergunta a um resolver específico"],
            "NXDOMAIN = o nome não existe no DNS. Causa clássica de 'não abre o sistema'."),

    # ---------------- LINUX: permissões ----------------
    Command("chmod", "linux", "permissões", "muda permissões de um arquivo", "chmod <modo> <arquivo>",
            ["chmod +x script.sh  → torna executável",
             "chmod 644 arq  → dono lê/escreve, resto só lê"]),
    Command("chown", "linux", "permissões", "muda o dono de um arquivo", "chown usuário:grupo <arquivo>",
            ["sudo chown kali:kali arq"]),
    Command("sudo", "linux", "permissões", "executa um comando como root (admin)", "sudo <comando>",
            [], "use só quando o comando realmente precisa de privilégio."),

    # ---------------- LINUX: firewall (ufw) ----------------
    Command("ufw", "linux", "firewall", "firewall simples do Debian/Ubuntu (Uncomplicated Firewall)", "sudo ufw <ação>",
            ["sudo ufw status verbose  → estado e regras",
             "sudo ufw status numbered  → regras com número (pra deletar)",
             "sudo ufw default deny incoming  → bloqueia tudo que entra",
             "sudo ufw default allow outgoing  → libera tudo que sai",
             "sudo ufw allow ssh  → libera uma porta (ou http, https)",
             "sudo ufw allow from 192.168.56.1 to any port 22 proto tcp  → só um IP",
             "sudo ufw delete allow ssh  → remove uma regra",
             "sudo ufw enable / disable  → liga / desliga"],
            "postura clássica: deny incoming + allow outgoing, e libere só o que precisa."),

    # ---------------- LINUX: pacotes (Debian/Kali) ----------------
    Command("apt update", "linux", "pacotes", "atualiza a lista de pacotes disponíveis", "sudo apt update"),
    Command("apt install", "linux", "pacotes", "instala um programa", "sudo apt install <pacote>",
            ["sudo apt install ufw -y  → -y responde 'sim' automaticamente"]),
    Command("apt search", "linux", "pacotes", "procura um pacote pelo nome", "apt search <termo>"),

    # ---------------- LINUX: compactação ----------------
    Command("tar", "linux", "arquivos", "empacota/desempacota .tar(.gz)", "tar [opções] arquivo.tar.gz [alvo]",
            ["tar czf pkg.tar.gz pasta/  → compacta (c=cria z=gzip f=arquivo)",
             "tar xzf pkg.tar.gz  → extrai (x=extrai)"]),

    # ================= GIT: config =================
    Command("git config", "git", "config", "define quem você é (nome/email) e preferências", "git config --global <chave> <valor>",
            ["git config --global user.name 'seu-nome'",
             "git config --global user.email 'voce@email.com'"],
            "--global vale pra todos os repos; sem ele, só pro repo atual."),

    # ================= GIT: básico =================
    Command("git init", "git", "básico", "cria um repositório git na pasta atual", "git init",
            [], "cria a pasta oculta .git/ — a partir daí é um repo."),
    Command("git clone", "git", "básico", "baixa um repositório existente", "git clone <url>",
            ["git clone https://github.com/user/repo.git"]),
    Command("git status", "git", "básico", "mostra o que mudou e o que está staged", "git status",
            ["git status -s  → versão curta"]),
    Command("git add", "git", "básico", "prepara mudanças pro próximo commit (staging)", "git add <arquivo | -A>",
            ["git add -A  → tudo", "git add arquivo.py  → só um"]),
    Command("git commit", "git", "básico", "grava as mudanças staged no histórico", "git commit -m 'mensagem'",
            ["git commit -m 'corrige login'"],
            "commit é LOCAL — não sobe pro GitHub sozinho (isso é o push)."),

    # ================= GIT: branches =================
    Command("git branch", "git", "branches", "lista/cria/apaga branches", "git branch [nome]",
            ["git branch  → lista (* marca o atual)",
             "git branch -M main  → renomeia o atual pra main"]),
    Command("git switch", "git", "branches", "troca de branch (moderno)", "git switch <branch>",
            ["git switch -c nova  → cria e já entra nela"]),
    Command("git checkout", "git", "branches", "troca de branch/versão (clássico)", "git checkout <branch>",
            [], "git switch é a forma nova e mais clara de trocar de branch."),
    Command("git merge", "git", "branches", "junta outra branch na atual", "git merge <branch>"),

    # ================= GIT: remoto =================
    Command("git remote", "git", "remoto", "gerencia os repositórios remotos (URLs)", "git remote <ação>",
            ["git remote -v  → mostra as URLs",
             "git remote add origin <url>  → liga ao GitHub"]),
    Command("git push", "git", "remoto", "envia seus commits pro remoto (GitHub)", "git push [-u origin main]",
            ["git push -u origin main  → 1ª vez (liga o branch)",
             "git push  → nas próximas"],
            "push usa a URL + autenticação (token, não senha)."),
    Command("git pull", "git", "remoto", "traz e junta o que mudou no remoto", "git pull"),
    Command("git fetch", "git", "remoto", "traz o que mudou no remoto SEM juntar ainda", "git fetch"),

    # ================= GIT: histórico =================
    Command("git log", "git", "histórico", "mostra o histórico de commits", "git log",
            ["git log --oneline  → um commit por linha",
             "git log --oneline --graph  → com desenho das branches"]),
    Command("git diff", "git", "histórico", "mostra as diferenças (o que mudou)", "git diff",
            ["git diff  → mudanças ainda não staged",
             "git diff --staged  → o que já está staged"]),
    Command("git show", "git", "histórico", "mostra os detalhes de um commit", "git show <hash>"),

    # ================= GIT: desfazer =================
    Command("git restore", "git", "desfazer", "desfaz mudanças em arquivos", "git restore <arquivo>",
            ["git restore arq  → descarta edição não-staged",
             "git restore --staged arq  → tira do staging (sem perder a edição)"]),
    Command("git reset", "git", "desfazer", "move o branch / desfaz commits", "git reset [--soft|--hard] <ref>",
            ["git reset --soft HEAD~1  → desfaz último commit, mantém mudanças"],
            "--hard APAGA as mudanças; use com cuidado."),
    Command("git revert", "git", "desfazer", "cria um commit que desfaz outro (seguro)", "git revert <hash>",
            [], "revert é o jeito seguro de desfazer algo que já subiu."),
    Command("git rm --cached", "git", "desfazer", "para de versionar um arquivo (mantém no disco)", "git rm --cached <arquivo>",
            ["git rm --cached .env  → tira do git mas não apaga o arquivo"]),

    # ================= GIT: stash =================
    Command("git stash", "git", "stash", "guarda mudanças temporariamente", "git stash",
            ["git stash  → guarda e limpa a área de trabalho",
             "git stash pop  → traz de volta"]),

    # ================= DOCKER: rodar =================
    Command("docker run", "docker", "rodar", "cria um container NOVO e roda a imagem", "docker run [opções] <imagem>",
            ["sudo docker run hello-world  → teste rápido",
             "sudo docker run -it ubuntu bash  → cria e entra (interativo)",
             "sudo docker run -d nginx  → em segundo plano (detached)",
             "sudo docker run -d -p 8080:80 --name web nginx  → porta host:container + nome"],
            "run SEMPRE cria container novo. Pra religar um existente use 'docker start'."),

    # ================= DOCKER: ver =================
    Command("docker ps", "docker", "ver", "lista containers", "docker ps [-a]",
            ["docker ps  → só os que estão rodando (Up)",
             "docker ps -a  → todos (rodando + parados/Exited)"],
            "um container fica Up enquanto o processo principal roda; nginx fica Up, 'bash' sai (Exited) no exit."),
    Command("docker images", "docker", "ver", "lista as imagens baixadas/criadas", "docker images"),
    Command("docker logs", "docker", "ver", "mostra a saída de um container", "docker logs <container>",
            ["docker logs web  → ex.: o access log do nginx"]),

    # ================= DOCKER: ciclo de vida =================
    Command("docker stop", "docker", "ciclo de vida", "desliga um container (vira Exited, não some)", "docker stop <container>"),
    Command("docker start", "docker", "ciclo de vida", "religa um container existente", "docker start <container>",
            [], "start REAPROVEITA o mesmo container/ID — não cria outro (diferente do run)."),
    Command("docker exec", "docker", "ciclo de vida", "entra/roda algo num container VIVO", "docker exec -it <container> bash",
            ["docker exec -it web bash  → abre um shell dentro do container"],
            "sair com 'exit' NÃO mata o container (diferente de um 'run -it')."),

    # ================= DOCKER: faxina =================
    Command("docker rm", "docker", "faxina", "apaga um container PARADO", "docker rm <container>",
            ["docker container prune  → apaga todos os parados de uma vez (respeita os Up)"]),
    Command("docker rmi", "docker", "faxina", "apaga uma IMAGEM", "docker rmi <imagem>",
            [], "rm = containers · rmi = imagens. Não dá pra apagar imagem em uso por um container."),

    # ================= DOCKER: criar imagem =================
    Command("docker build", "docker", "imagem", "constrói uma imagem a partir de um Dockerfile", "docker build -t <nome> .",
            ["sudo docker build -t meu-site .  → -t dá o nome; o '.' = esta pasta (não esqueça o ponto!)"],
            "ciclo mental: escrever arquivos → Dockerfile → build → run."),
    Command("Dockerfile", "docker", "imagem", "a receita pra construir uma imagem", "FROM <base> ; COPY <origem> <destino>",
            ["FROM nginx:alpine  → herda de uma imagem base",
             "COPY . /usr/share/nginx/html  → põe seus arquivos dentro da imagem"],
            "FROM = base que você herda · COPY = leva seus arquivos pra dentro da imagem."),
]
