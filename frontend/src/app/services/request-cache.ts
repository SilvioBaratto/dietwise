// src/app/services/request-cache.ts
import { Observable, catchError, shareReplay, throwError } from 'rxjs';

/**
 * In-memory, per-session cache for GET-style Observables. Two concurrent
 * callers for the same key share one HTTP request (Map holds the shared
 * Observable itself, not just the resolved value). A failed request evicts
 * its own key so the next call retries against the network instead of
 * replaying the same error for the rest of the session.
 */
export class RequestCache<T> {
  private readonly entries = new Map<string, Observable<T>>();

  get(key: string, factory: () => Observable<T>): Observable<T> {
    const cached = this.entries.get(key);
    if (cached) {
      return cached;
    }

    const shared$ = factory().pipe(
      catchError((err) => {
        this.entries.delete(key);
        return throwError(() => err);
      }),
      shareReplay({ bufferSize: 1, refCount: false }),
    );
    this.entries.set(key, shared$);
    return shared$;
  }

  delete(key: string): void {
    this.entries.delete(key);
  }

  clear(): void {
    this.entries.clear();
  }
}
