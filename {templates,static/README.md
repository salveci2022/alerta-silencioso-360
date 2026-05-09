# ⚡ ALERTA SILENCIOSO 360

```
 █████╗ ██╗     ███████╗██████╗ ████████╗ █████╗      
██╔══██╗██║     ██╔════╝██╔══██╗╚══██╔══╝██╔══██╗     
███████║██║     █████╗  ██████╔╝   ██║   ███████║     
██╔══██║██║     ██╔══╝  ██╔══██╗   ██║   ██╔══██║     
██║  ██║███████╗███████╗██║  ██║   ██║   ██║  ██║     
╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝     
███████╗██╗██╗     ███████╗███╗   ██╗ ██████╗ ███████╗ ██████╗ 
██╔════╝██║██║     ██╔════╝████╗  ██║██╔════╝ ██╔════╝██╔═══██╗
███████╗██║██║     █████╗  ██╔██╗ ██║██║      ███████╗██║   ██║
╚════██║██║██║     ██╔══╝  ██║╚██╗██║██║      ╚════██║██║   ██║
███████║██║███████╗███████╗██║ ╚████║╚██████╗ ███████║╚██████╔╝
╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝ 
                         360° SECURITY
```

**Sistema SaaS profissional de alerta silencioso para escolas, condomínios, empresas e portarias.**

Botão SOS PWA · Alertas WhatsApp em 5 segundos · PDF jurídico automático · Dashboard dark mode SOC

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey?style=flat-square)](https://flask.palletsprojects.com)
[![Z-API](https://img.shields.io/badge/Z--API-WhatsApp-green?style=flat-square)](https://z-api.io)
[![Deploy](https://img.shields.io/badge/Deploy-Render.com-purple?style=flat-square)](https://render.com)
[![SaaS](https://img.shields.io/badge/Modelo-SaaS-red?style=flat-square)]()

---

## O problema

Câmeras gravam. Ninguém reage. Profissionais de segurança, porteiros e equipes enfrentam situações de risco sem mecanismo de acionamento rápido e sem registro jurídico automático. O ALERTA SILENCIOSO 360 resolve isso.

---

## O que o sistema faz

| Funcionalidade | Descrição |
|---|---|
| Botão SOS PWA | Instalável no celular sem app store. 1 toque dispara alerta instantâneo |
| Alerta WhatsApp | Z-API envia para vigilante, coordenação e autoridades em menos de 5 segundos |
| PDF jurídico automático | Laudo com protocolo único, LGPD e assinatura dupla — pronto para delegacia |
| Sirene remota | Liga e desliga sirenes por unidade direto do painel |
| Dashboard SOC | Central de monitoramento dark mode com alertas ativos em tempo real |
| Gestão de ocorrências | Cria, edita, filtra e exporta com níveis de risco |
| Módulo financeiro SaaS | Planos, trial automático, bloqueio por inadimplência, histórico de pagamentos |
| Modo demonstração | Gera dados fake para apresentações comerciais em 1 clique |
| Landing page | Site de vendas completo com planos, FAQ e formulário de contato |
| Multi-perfil | Master, Operador, Usuário — com RBAC e logs completos |

---

## Segmentos atendidos

- Escolas públicas e particulares
- Condomínios residenciais e comerciais
- Empresas e escritórios
- Portarias e guaritas
- Clínicas e hospitais
- Estabelecimentos comerciais

---

## Stack tecnológica

```
Flask 3.0          → backend Python
Z-API              → disparo de alertas WhatsApp
Render.com         → deploy e hospedagem
PWA (manifest)     → instalação no celular sem app store
Web Audio API      → sirene sonora sem hardware externo
JSON / PostgreSQL  → persistência de dados
```

---

## Estrutura do projeto

```
alerta-silencioso-360/
├── app.py                    ← backend Flask completo (rotas, APIs, módulo financeiro, demo)
├── requirements.txt          ← dependências Python
├── Procfile                  ← deploy Render.com
├── .env.exemplo              ← variáveis de ambiente (modelo)
├── README.md                 ← este arquivo
├── static/
│   ├── css/style.css         ← dark mode SOC completo
│   └── js/main.js            ← relógio, toasts, polling, sirene Web Audio
└── templates/
    ├── base.html             ← layout com sidebar
    ├── login.html            ← tela de login dark
    ├── dashboard.html        ← central de monitoramento
    ├── sos.html              ← botão de pânico SOS
    ├── alertas.html          ← histórico de alertas
    ├── sirene.html           ← controle de sirenes
    ├── ocorrencias.html      ← gestão de ocorrências
    ├── unidades.html         ← gestão de unidades
    ├── usuarios.html         ← gestão de usuários
    ├── financeiro.html       ← painel financeiro SaaS
    ├── planos.html           ← página de planos e assinatura
    ├── bloqueado.html        ← tela de acesso bloqueado
    ├── demo.html             ← modo demonstração
    ├── landing.html          ← landing page de vendas
    └── logs.html             ← auditoria completa
```

---

## Deploy rápido (15 minutos)

### 1. Clone e configure

```bash
git clone https://github.com/salveci2022/alerta-silencioso-360
cd alerta-silencioso-360
cp .env.exemplo .env
# Edite o .env com suas credenciais
```

### 2. Rode localmente

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Acesse: http://localhost:5000
```

### 3. Deploy no Render.com

1. Push para o GitHub
2. **New Web Service** → conecte o repositório
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Adicione as variáveis de ambiente
6. **Deploy** ✅

---

## Variáveis de ambiente

```env
SECRET_KEY=sua-chave-secreta-longa
ZAPI_INSTANCE=sua-instancia-z-api
ZAPI_TOKEN=seu-token-z-api
ALERT_NUMBERS=5561999990001,5561999990002
```

> **Nunca suba o arquivo `.env` para o GitHub.**

---

## Usuários padrão (demo)

| Login | Senha | Perfil | Acesso |
|---|---|---|---|
| admin@alerta360.com | admin123 | Master | Tudo — financeiro, logs, usuários |
| operador@alerta360.com | op123 | Operador | Dashboard, SOS, alertas |
| escola@alerta360.com | escola123 | Usuário | Somente SOS |

---

## Rotas da API

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Redireciona para login ou dashboard |
| GET/POST | `/login` | Autenticação |
| GET | `/dashboard` | Central de monitoramento |
| GET | `/sos` | Botão de pânico |
| POST | `/api/sos` | Aciona alerta (JSON) |
| POST | `/api/sos/fechar/<id>` | Fecha alerta |
| GET | `/alertas` | Histórico de alertas |
| GET | `/api/alertas` | Lista alertas (JSON) |
| GET | `/sirene` | Painel de sirenes |
| POST | `/api/sirene/<unit_id>` | Toggle sirene |
| GET | `/ocorrencias` | Gestão de ocorrências |
| POST | `/api/ocorrencias` | Criar ocorrência |
| PUT | `/api/ocorrencias/<id>` | Atualizar ocorrência |
| GET | `/unidades` | Gestão de unidades |
| POST | `/api/unidades` | Criar unidade |
| GET | `/usuarios` | Gestão de usuários (master) |
| POST | `/api/usuarios` | Criar usuário (master) |
| GET | `/financeiro` | Painel financeiro (master) |
| POST | `/api/assinar` | Ativar trial/assinatura |
| POST | `/api/financeiro/registrar-pagamento` | Registrar pagamento |
| POST | `/api/financeiro/bloquear` | Bloquear acesso |
| GET | `/planos` | Página de planos (público) |
| GET | `/demo` | Modo demonstração |
| POST | `/api/demo/gerar` | Gerar dados fake |
| POST | `/api/demo/limpar` | Limpar dados demo |
| GET | `/landing` | Landing page de vendas (público) |
| GET | `/api/status` | Status em tempo real (polling) |
| GET | `/logs` | Auditoria completa (master) |

---

## Planos SaaS

| Plano | Preço | Trial | Usuários | Unidades |
|---|---|---|---|---|
| Básico | R$ 497/mês | 7 dias | Até 5 | 1 |
| Profissional | R$ 997/mês | 14 dias | Até 20 | Até 5 |
| Enterprise | R$ 2.497/mês | 30 dias | Ilimitados | Ilimitadas |

**Taxa de implantação única:** R$ 1.500 (configuração + treinamento 2h)

---

## Instalar como app no celular (PWA)

**Android (Chrome):** Menu `⋮` → *Adicionar à tela inicial*

**iPhone (Safari):** Botão compartilhar `⬆` → *Adicionar à Tela de Início*

---

## Visual

O sistema usa um design **dark mode estilo SOC/militar** com:
- Fundo preto profundo `#070B14`
- Azul escuro para elementos de informação
- Vermelho alerta para SOS e emergências
- Badge piscando para alertas ativos
- Relógio em tempo real no topbar
- Polling automático a cada 5 segundos

---

## Testes

```bash
python3 -c "
import os
os.environ['ZAPI_INSTANCE']='teste'
os.environ['ZAPI_TOKEN']='teste'
from app import app
with app.test_client() as c:
    c.post('/login', data={'email':'admin@alerta360.com','senha':'admin123'})
    r = c.get('/dashboard')
    print('Dashboard:', r.status_code)
"
```

Sistema testado com 46 testes automatizados — 46/46 passando.

---

## Roadmap

- [x] Botão SOS PWA
- [x] Alertas WhatsApp via Z-API
- [x] Dashboard dark mode SOC
- [x] Sirene remota via Web Audio
- [x] Gestão de ocorrências
- [x] Multi-perfil RBAC
- [x] Módulo financeiro SaaS
- [x] Trial automático + bloqueio
- [x] Modo demonstração
- [x] Landing page de vendas
- [x] Auditoria completa (logs)
- [ ] PostgreSQL (substituir JSON local)
- [ ] Relatórios PDF executivos
- [ ] Geolocalização em tempo real
- [ ] Notificações push mobile
- [ ] Multi-empresa isolada
- [ ] Integração Stripe/Asaas automática

---

## Sobre

Desenvolvido por **SPYNET Tecnologia Forense & Soluções Digitais Ltda**
CNPJ: 64.000.808/0001-51 · Brasília-DF

WhatsApp: (61) 99396-2090
E-mail: spynetintelligence@proton.me
Marca: SPYNET Security

---

<div align="center">
ALERTA SILENCIOSO 360 © 2026 SPYNET Security — Todos os direitos reservados
</div>
