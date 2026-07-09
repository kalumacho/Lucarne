"use client";

import { useState } from "react";
import { createClient } from "../lib/supabase/client";
import styles from "../compte/compte.module.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent" | "error">(
    "idle",
  );

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setState("sending");
    const supabase = createClient();
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${location.origin}/auth/callback` },
    });
    setState(error ? "error" : "sent");
  }

  return (
    <main className={styles.wrap}>
      <a className={styles.back} href="/">
        ← Retour aux consultations
      </a>
      <h1 className={styles.title}>Créer mon radar local</h1>
      <p className={styles.lead}>
        Entrez votre e-mail : vous recevrez un lien de connexion, sans mot de
        passe. Vous pourrez ensuite indiquer votre commune pour voir en priorité
        les consultations près de chez vous.
      </p>

      {state === "sent" ? (
        <p className={styles.success}>
          Lien envoyé à <strong>{email}</strong>. Ouvrez votre boîte mail pour
          vous connecter.
        </p>
      ) : (
        <form className={styles.form} onSubmit={submit}>
          <label className={styles.label}>
            E-mail
            <input
              className={styles.input}
              type="email"
              required
              autoComplete="email"
              placeholder="vous@exemple.fr"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <button
            className={styles.button}
            type="submit"
            disabled={state === "sending"}
          >
            {state === "sending" ? "Envoi…" : "Recevoir mon lien"}
          </button>
          {state === "error" && (
            <p className={styles.error}>
              Envoi impossible. Vérifiez l’adresse et réessayez.
            </p>
          )}
        </form>
      )}
    </main>
  );
}
