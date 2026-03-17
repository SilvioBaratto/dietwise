// ============================================================
// Test cases for diet.baml functions — one per function
// ============================================================


// Full week, weight loss, all params provided
test GeneraDietaSettimanale_SettimanaCompleta {
  functions [GeneraDietaSettimanale]
  args {
    dataInizio "2026-03-23"
    giornoInizio "LUNEDI"
    dataFine "2026-03-29"
    giornoFine "DOMENICA"
    peso 90.0
    altezza 178.0
    eta 38
    sesso "maschio"
    obiettivo "perdere peso"
    altri_dati "Nessuna restrizione alimentare. Preferisce pasti veloci a pranzo (max 20 minuti di preparazione). Fa palestra 3 volte a settimana (lunedì, mercoledì, venerdì)."
  }
}


// Multi-day grocery list with ingredient overlap for aggregation testing
test GeneraListaSpesa_PastiMultigiorno {
  functions [GeneraListaSpesa]
  args {
    pasti [
      {
        giorno LUNEDI
        tipo COLAZIONE
        nome "Porridge di avena con banana e mandorle"
        orario "07:30"
        ingredienti "Fiocchi d'avena 80g, latte parzialmente scremato 250ml, banana 1 pz, mandorle 20g, miele 10g"
        calorie 450
        proteine 14
        carboidrati 68
        grassi 13
      }
      {
        giorno LUNEDI
        tipo PRANZO
        nome "Pasta integrale al pomodoro con pollo"
        orario "13:00"
        ingredienti "Pasta integrale 80g, petto di pollo 150g, pomodori pelati 200g, olio extravergine d'oliva 10ml, basilico fresco 5g, aglio 1 pz"
        calorie 520
        proteine 42
        carboidrati 62
        grassi 9
      }
      {
        giorno LUNEDI
        tipo CENA
        nome "Salmone al forno con verdure grigliate e riso basmati"
        orario "19:30"
        ingredienti "Filetto di salmone 180g, riso basmati 70g, zucchine 150g, peperoni 100g, olio extravergine d'oliva 10ml, limone 1 pz, rosmarino 2g"
        calorie 580
        proteine 38
        carboidrati 58
        grassi 18
      }
      {
        giorno MARTEDI
        tipo COLAZIONE
        nome "Uova strapazzate con pane integrale e pomodorini"
        orario "07:30"
        ingredienti "Uova 2 pz, pane integrale 60g, pomodorini 100g, olio extravergine d'oliva 5ml, sale q.b."
        calorie 390
        proteine 22
        carboidrati 40
        grassi 14
      }
      {
        giorno MARTEDI
        tipo PRANZO
        nome "Insalata di farro con tonno e verdure"
        orario "13:00"
        ingredienti "Farro 80g, tonno in acqua 120g, cetriolo 100g, pomodorini 120g, olive nere 20g, olio extravergine d'oliva 10ml, limone 1 pz"
        calorie 490
        proteine 36
        carboidrati 55
        grassi 13
      }
      {
        giorno MARTEDI
        tipo CENA
        nome "Pollo arrosto con patate e insalata verde"
        orario "19:30"
        ingredienti "Coscia di pollo 200g, patate 200g, insalata mista 100g, olio extravergine d'oliva 10ml, rosmarino 3g, aglio 2 pz, sale q.b."
        calorie 560
        proteine 40
        carboidrati 48
        grassi 18
      }
    ]
  }
}


// Replace Thursday dinner with blue fish
test ModificaDietaSettimanale_SostituisciCenaGiovedi {
  functions [ModificaDietaSettimanale]
  args {
    dietaCorrente {
      nome "Piano Dimagrimento Settimanale — Marco, 38 anni"
      dataInizio "2026-03-23"
      dataFine "2026-03-29"
      pasti [
        {
          giorno LUNEDI
          tipo COLAZIONE
          nome "Porridge di avena con banana"
          orario "07:30"
          ingredienti "Fiocchi d'avena 80g, latte 250ml, banana 1 pz, miele 10g"
          calorie 420
          proteine 13
          carboidrati 72
          grassi 8
        }
        {
          giorno LUNEDI
          tipo PRANZO
          nome "Pasta integrale al ragù di tacchino"
          orario "13:00"
          ingredienti "Pasta integrale 80g, macinato di tacchino 150g, pomodori pelati 200g, carote 50g, sedano 30g, cipolla 40g, olio EVO 10ml"
          calorie 540
          proteine 40
          carboidrati 65
          grassi 11
        }
        {
          giorno LUNEDI
          tipo CENA
          nome "Branzino al forno con verdure"
          orario "19:30"
          ingredienti "Branzino 200g, zucchine 150g, pomodorini 100g, olio EVO 10ml, limone 1 pz, timo 2g"
          calorie 380
          proteine 36
          carboidrati 12
          grassi 20
        }
        {
          giorno GIOVEDI
          tipo COLAZIONE
          nome "Porridge di avena con frutti di bosco"
          orario "07:30"
          ingredienti "Fiocchi d'avena 80g, latte 250ml, frutti di bosco misti 100g"
          calorie 390
          proteine 13
          carboidrati 65
          grassi 7
        }
        {
          giorno GIOVEDI
          tipo PRANZO
          nome "Insalata di farro con verdure grigliate"
          orario "13:00"
          ingredienti "Farro 80g, melanzane 150g, peperoni 100g, pomodorini 100g, olio EVO 10ml, basilico 5g"
          calorie 430
          proteine 14
          carboidrati 68
          grassi 11
        }
        {
          giorno GIOVEDI
          tipo CENA
          nome "Pollo alla griglia con insalata"
          orario "19:30"
          ingredienti "Petto di pollo 180g, insalata mista 150g, pomodorini 80g, olio EVO 10ml, limone 1 pz"
          calorie 370
          proteine 42
          carboidrati 10
          grassi 16
        }
      ]
    }
    richiestaModifica "Vorrei sostituire la cena di giovedì con qualcosa a base di pesce azzurro (sgombro o sardine). Preferisco qualcosa di caldo come una zuppa o al forno."
    peso 90.0
    altezza 178.0
    eta 38
    sesso "maschio"
    obiettivo "perdere peso"
    oggiData "2026-03-25"
    oggiGiorno "MERCOLEDI"
  }
}


// Recipe for a CENA — baked salmon
test GeneraRicetta_Cena_SalmoneAlForno {
  functions [GeneraRicetta]
  args {
    pasto {
      giorno LUNEDI
      tipo CENA
      nome "Salmone al forno con verdure mediterranee e riso basmati"
      orario "19:30"
      ingredienti "Filetto di salmone atlantico 180g, riso basmati 70g, zucchine 150g, peperoni rossi 100g, pomodorini 80g, olio extravergine d'oliva 10ml, succo di limone 1 pz, rosmarino fresco 2g, aglio 1 pz"
      calorie 580
      proteine 38
      carboidrati 58
      grassi 18
    }
  }
}
