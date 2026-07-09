"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../lib/supabase/client";
import { cpToDepartement, departementName } from "../lib/departements";
import styles from "./compte.module.css";

type Props = { email: string; ville: string; codePostal: string };

export default function ProfileForm({ email, ville, codePostal }: Props) {
  const router = useRouter();
  const [v, setV] = useState(ville);
  const [cp, setCp] = useState(codePostal);
  const [state, setState] = useState<"idle" | "saving" | "saved" | "error">(
    "idle",
  );

  const dept = cpToDepartement(cp);
  const deptLabel = departementName(dept);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setState("saving");
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();
    if (!user) {
      setState("error");
      return;
    }
    const { error } = await supabase.from("profiles").upsert({
      id: user.id,
      ville: v.trim(),
      code_postal: cp.trim(),
      departement: dept,
      updated_at: new Date().toISOString(),
    });
    if (error) {
      setState("error");
    } else {
      setState("saved");
      router.refresh();
    }
  }

  async function logout() {
    await createClient().auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <form className={styles.form} onSubmit={save}>
      <p className={styles.identity}>Connecté en tant que {email}</p>

      <label className={styles.label}>
        Ville
        <input
          className={styles.input}
          type="text"
          required
          placeholder="Ex. Faremoutiers"
          value={v}
          onChange={(e) => setV(e.target.value)}
        />
      </label>

      <label className={styles.label}>
        Code postal
        <input
          className={styles.input}
          type="text"
          inputMode="numeric"
          required
          pattern="\d{4,5}"
          placeholder="Ex. 77515"
          value={cp}
          onChange={(e) => setCp(e.target.value)}
        />
      </label>

      {deptLabel && (
        <p className={styles.hint}>
          Département détecté&nbsp;: <strong>{deptLabel}</strong> ({dept})
        </p>
      )}

      <button className={styles.button} type="submit" disabled={state === "saving"}>
        {state === "saving" ? "Enregistrement…" : "Enregistrer"}
      </button>

      {state === "saved" && (
        <p className={styles.success}>
          Enregistré. <a href="/">Voir mes consultations locales →</a>
        </p>
      )}
      {state === "error" && (
        <p className={styles.error}>Échec de l’enregistrement. Réessayez.</p>
      )}

      <button type="button" className={styles.logout} onClick={logout}>
        Se déconnecter
      </button>
    </form>
  );
}
