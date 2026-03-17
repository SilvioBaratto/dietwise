enum GiornoSettimana {
  LUNEDI
  MARTEDI
  MERCOLEDI
  GIOVEDI
  VENERDI
  SABATO
  DOMENICA
}

enum TipoPasto {
  COLAZIONE
  SPUNTINO_MATTINA
  PRANZO
  SPUNTINO_POMERIGGIO
  CENA
}

enum UnitaMisura {
  KG
  GR
  L
  ML
  PZ
}

class Ingrediente {
  nome string
  quantita float
  unita UnitaMisura
}

class Pasto {
  tipo TipoPasto
  nome string
  orario string @description("Orario del pasto")
  ingredienti string
  calorie int
}

class Dieta {
  giorno GiornoSettimana
  pasti Pasto[]
}

class DietaSettimanale {
  nome string
  dataInizio string @description("YYYY-MM-DD")
  dataFine string @description("YYYY-MM-DD")
  dieta Dieta[] @description("Elenco dei giorni della settimana con i relativi pasti")
}

function GeneraDietaSettimanale(
  dataInizio: string,
  giornoInizio: string,
  dataFine: string,
  giornoFine: string,
  peso: float,
  altezza: float,
  eta: int?,
  sesso: string?,
  obiettivo: string,
  altri_dati: string
) -> DietaSettimanale {
  client OpenAI
  prompt #"
    {{ _.role("system") }}
    Sei un dietologo clinico certificato specializzato in nutrizione personalizzata evidence-based.

    {{ _.role("user") }}

    DATI ANTROPOMETRICI:
    - Peso: {{ peso }}kg, Altezza: {{ altezza }}cm
    - Età: {% if eta %}{{ eta }}{% else %}30{% endif %} anni, Sesso: {% if sesso %}{{ sesso }}{% else %}non specificato{% endif %}
    - BMI: {{ (peso / ((altezza/100) ** 2)) | round(1) }}

    CALCOLO FABBISOGNO (Mifflin-St Jeor):
    - BMR stimato + TDEE per obiettivo: {{ obiettivo }}
    - AMDR target: Carb 45-55%, Prot 20-25%, Grassi 25-30%

    REQUISITI PIANO:
    - Nome descrittivo con obiettivo e durata
    - Periodo: Dal {{ dataInizio }} ({{ giornoInizio }}) al {{ dataFine }} ({{ giornoFine }})
    - IMPORTANTE: Genera pasti SOLO per i giorni da {{ giornoInizio }} a {{ giornoFine }} inclusi
    - NON includere giorni prima di {{ giornoInizio }} o dopo {{ giornoFine }}
    - 5 pasti/die (COLAZIONE, SPUNTINO_MATTINA, PRANZO, SPUNTINO_POMERIGGIO, CENA) con orari realistici
    - Ingredienti: "Nome Quantità+Unità" (g, ml, pz)
    - Calorie per pasto bilanciate per timing metabolico
    - Varietà quotidiana minima 60% ingredienti
    - Include fibre (25-30g/die) e micronutrienti essenziali

    INFORMAZIONI AGGIUNTIVE:
    {{ altri_dati }}

    {{ ctx.output_format(prefix='Restituisci una dieta con questa struttura:') }}
  "#
}

class ListaSpesa {
  ingredienti Ingrediente[] @description("Elenco aggregato di tutti gli ingredienti da acquistare per l'intera settimana, con quantità sommate e unità di misura coerenti")
}

function GeneraListaSpesa(
  dieta: Dieta[]
) -> ListaSpesa {
  client OpenAI
  prompt #"
    {{ _.role("system") }}
    Sei un sistema di ottimizzazione nutrizionale per la pianificazione alimentare.

    {{ _.role("user") }}

    ALGORITMO AGGREGAZIONE SCIENTIFICA:
    1. RAGGRUPPA ingredienti identici (fuzzy matching 90%)
    2. SOMMA quantità mantenendo precisione nutrizionale
    3. CONVERTI unità dove appropriato (1000g → 1kg, 1000ml → 1L, evita rappresentare in kg o litri se sotto 1000g/ml per facilità d'uso)
    4. ARROTONDA considerando shelf-life e porzioni commerciali:
       - Proteine: multipli 100g
       - Verdure: multipli 250g
       - Liquidi: formati standard (500ml, 1L)
    5. CATEGORIZZA per gruppo alimentare (proteine, carboidrati, verdure, frutta, condimenti, altro)

    PASTI SETTIMANALI DA AGGREGARE:

    {% for giorno_dieta in dieta %}
    ### {{ giorno_dieta.giorno }}

    | Tipo Pasto | Ingredienti |
    |------------|-------------|
    {% for pasto in giorno_dieta.pasti %}
    | {{ pasto.tipo }} | {{ pasto.ingredienti }} |
    {% endfor %}

    {% endfor %}

    {{ ctx.output_format(prefix='Restituisci la lista della spesa con questa struttura:') }}
  "#
}

function ModificaDietaSettimanale(
  dietaCorrente: DietaSettimanale,
  richiestaModifica: string,
  peso: float,
  altezza: float,
  eta: int?,
  sesso: string?,
  obiettivo: string,
  oggiData: string,
  oggiGiorno: string
) -> DietaSettimanale {
  client OpenAI
  prompt #"
    {{ _.role("system") }}
    Sei un dietologo specializzato in modifiche terapeutiche e ottimizzazione piani nutrizionali.

    {{ _.role("user") }}

    VALUTAZIONE STATO ATTUALE:
    - BMR base: {{ peso }}kg × {{ altezza }}cm, età {{ eta|default(30) }}{% if sesso %}, sesso {{ sesso }}{% endif %}
    - BMI: {{ (peso / ((altezza/100) ** 2)) | round(1) }}
    - Piano: {{ dietaCorrente.nome }} ({{ dietaCorrente.dataInizio }} - {{ dietaCorrente.dataFine }})
    - Obiettivo iniziale: {{ obiettivo }}

    DATA ODIERNA:
    Oggi è {{ oggiGiorno }} {{ oggiData }}

    ANALISI PASTI CORRENTI:

    | Giorno | Tipo Pasto | Orario | Nome Pasto | Calorie | Ingredienti |
    |--------|------------|--------|------------|---------|-------------|
    {% for giorno in dietaCorrente.dieta %}
    {% for pasto in giorno.pasti %}
    | {{ giorno.giorno }} | {{ pasto.tipo }} | {{ pasto.orario }} | {{ pasto.nome }} | {{ pasto.calorie }}kcal | {{ pasto.ingredienti }} |
    {% endfor %}
    {% endfor %}

    RICHIESTA MODIFICA:
    {{ richiestaModifica }}

    PROTOCOLLO MODIFICA SCIENTIFICA:
    1. IDENTIFICA tipo modifica (specifica vs sistemica)
    2. CALCOLA impatto su bilancio energetico e AMDR
    3. PRESERVA timing nutrizionale (colazione anabolica, pranzo energetico, cena recupero)
    4. MANTIENI biodisponibilità nutrienti e sinergie alimentari
    5. ASSICURA compliance AMDR: Carb 45-65%, Prot 10-35%, Grassi 20-35%
    6. VERIFICA adeguatezza micronutrienti post-modifica
    7. APPLICA principio minima modifica per massima aderenza

    {{ ctx.output_format(prefix='Restituisci la dieta modificata seguendo questa struttura:') }}
  "#
}

class HtmlStructure {
  h1 string
  h2 string[]
  p string[]
  ul string[]
  ol string[]
}

function GeneraRicetta(
  pasto: Pasto
) -> HtmlStructure {
  client OpenAI
  prompt #"
    {{ _.role("system") }}
    Sei uno chef nutrizionista specializzato.

    {{ _.role("user") }}

    ANALISI PASTO:
    - Tipo: {{ pasto.tipo }}
    - Nome target: {{ pasto.nome }}
    - Calorie: {{ pasto.calorie }}kcal
    - Ingredienti disponibili: {{ pasto.ingredienti }}

    TIMING METABOLICO (basato sul tipo pasto):
    - COLAZIONE: anabolico mattutino
    - SPUNTINO_MATTINA: sostegno metabolico mattutino
    - PRANZO: picco energetico
    - SPUNTINO_POMERIGGIO: sostegno metabolico pomeridiano
    - CENA: recupero notturno

    VINCOLI ASSOLUTI:
    - USA ESCLUSIVAMENTE gli ingredienti elencati sopra
    - NON aggiungere ingredienti extra
    - NON suggerire sostituzioni

    STRUTTURA RICETTA OTTIMIZZATA:

    h1: {{ pasto.nome }}

    h2: Info Nutrizionali Quick
    p: Tempo preparazione e cottura stimato
    p: Calorie: {{ pasto.calorie }}kcal

    h2: Preparazione

    LINEE GUIDA:
    - Linguaggio chiaro e professionale
    - Istruzioni precise e sequenziali
    - Focus su tecniche che preservano nutrienti
    - Tono motivante ed educativo

    {{ ctx.output_format }}
  "#
}