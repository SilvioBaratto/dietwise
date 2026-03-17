// src/app/models/diet.types.ts

export interface TipoPasto {
  readonly tipo: 'COLAZIONE' | 'SPUNTINO_MATTINA' | 'PRANZO' | 'SPUNTINO_POMERIGGIO' | 'CENA';
  readonly orario?: string;
  readonly ricetta: string;
}

export interface Ingrediente {
  readonly nome: string;
  readonly quantita: number;
  readonly unita: string;
}

export interface Pasto {
  readonly id: string;
  readonly tipoPasto: TipoPasto;
  readonly ingredienti: string;  // Comma-separated ingredient string
  readonly calorie: number;
  readonly proteine: number;
  readonly carboidrati: number;
  readonly grassi: number;
  readonly day: string;  // BAML enum: "LUNEDI", "MARTEDI", etc.
}

export interface DietaSettimanale {
  readonly id: string;          // Diet ID
  readonly nome: string;
  readonly dataInizio: string;  // ISO "YYYY-MM-DD"
  readonly dataFine: string;    // ISO "YYYY-MM-DD"
  readonly pasti: Pasto[];
}

export interface ListaSpesa {
  readonly ingredienti: Ingrediente[];
}

export interface DietaConLista {
  readonly dieta: DietaSettimanale;
  readonly listaSpesa: ListaSpesa;
}

export interface DailyGroup {
  readonly date: string;     // "YYYY-MM-DD"
  readonly dayName: string;  // "lunedì", "martedì"… (it-IT)
  readonly meals: Pasto[];
}

export interface ModifyDietRequest {
  readonly modification_prompt: string;
}

export interface DietSummary {
  readonly id: string;
  readonly name?: string;
  readonly created_at: string;
}
