import { NextResponse, type NextRequest } from "next/server";
import { createClient } from "../../lib/supabase/server";

// Le lien magique renvoie ici avec ?code=… : on l'échange contre une session.
export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/compte";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }
  return NextResponse.redirect(`${origin}/login?erreur=lien`);
}
