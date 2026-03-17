// src/app/auth/pending-approval/pending-approval.component.ts
import { Component, inject, signal, computed, ChangeDetectionStrategy } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-pending-approval',
  templateUrl: './pending-approval.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PendingApprovalComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  // Get user email from session
  userEmail = computed(() => this.auth.sessionSubject.value?.user?.email || '[IL TUO INDIRIZZO EMAIL]');

  // Copy feedback
  copied = signal(false);

  // Email content
  emailTo = 'silvio.baratto22@gmail.com';
  emailSubject = 'Richiesta di Accesso a DietologoAI';

  emailBody = computed(() => `Gentile Titolare,

Con la presente, io sottoscritto/a, identificato/a tramite l'indirizzo email ${this.userEmail()}, richiedo formalmente l'accesso all'applicazione DietologoAI.

DICHIARAZIONI E ASSUNZIONI DI RESPONSABILITÀ:

1. CONSAPEVOLEZZA DEL SERVIZIO
Dichiaro di essere pienamente consapevole che DietologoAI è un'applicazione sperimentale che utilizza intelligenza artificiale per generare suggerimenti alimentari a scopo puramente informativo e di intrattenimento.

2. ESCLUSIONE DI CONSULENZA MEDICA
Dichiaro di comprendere e accettare che:
- L'applicazione NON fornisce consulenza medica, diagnosi o trattamenti
- I piani alimentari generati NON sostituiscono il parere di medici, dietisti, nutrizionisti o altri professionisti sanitari qualificati
- Prima di apportare qualsiasi modifica alla mia alimentazione, consulterò un professionista sanitario

3. ASSUNZIONE DI RESPONSABILITÀ
Assumo personalmente ogni responsabilità per:
- L'utilizzo dei contenuti generati dall'applicazione
- Eventuali conseguenze derivanti dal seguire i suggerimenti alimentari
- La verifica della compatibilità dei piani alimentari con le mie condizioni di salute

4. DICHIARAZIONE SULLO STATO DI SALUTE
Dichiaro di:
[ ] NON essere affetto/a da patologie che richiedono supervisione medica per l'alimentazione
[ ] NON essere in gravidanza o allattamento
[ ] Essere maggiorenne (età superiore a 18 anni)
[ ] NON soffrire di disturbi del comportamento alimentare
[ ] Aver consultato o impegnarmi a consultare un medico prima di seguire qualsiasi piano alimentare

(Sostituire [ ] con [X] per confermare ogni dichiarazione)

5. ESONERO DI RESPONSABILITÀ
Esonero espressamente il Titolare dell'applicazione da qualsiasi responsabilità per danni diretti, indiretti, consequenziali o di qualsiasi natura derivanti dall'uso dell'applicazione e dei suoi contenuti.

6. ACCETTAZIONE TERMINI
Dichiaro di aver letto, compreso e accettato integralmente i Termini e Condizioni di Utilizzo e l'Informativa Privacy disponibili nell'applicazione.

7. REVOCA ACCESSO
Prendo atto che il Titolare si riserva il diritto di revocare l'accesso in qualsiasi momento, senza obbligo di motivazione.

Cordiali saluti,

[INSERIRE NOME E COGNOME]
Email: ${this.userEmail()}
Data: ${new Date().toLocaleDateString('it-IT')}

---
Inviando questa email, confermo la veridicità delle dichiarazioni sopra riportate e accetto integralmente le condizioni di utilizzo dell'applicazione.`);

  copyToClipboard(): void {
    const fullEmail = `A: ${this.emailTo}\nOggetto: ${this.emailSubject}\n\n${this.emailBody()}`;
    navigator.clipboard.writeText(fullEmail).then(() => {
      this.copied.set(true);
      setTimeout(() => this.copied.set(false), 2000);
    });
  }

  async logout(): Promise<void> {
    await this.auth.signOut();
    this.router.navigate(['/login']);
  }
}
