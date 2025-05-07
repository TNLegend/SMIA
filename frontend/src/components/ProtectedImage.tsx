import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";

export function ProtectedImage({
  src, alt, style
}: {
  src: string;
  alt?: string;
  style?: React.CSSProperties;
}) {
  const { token } = useAuth();
  const [blobUrl, setBlobUrl] = useState<string>();

  useEffect(() => {
    let mounted = true;
    let objectUrl: string;
    fetch(src, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: "include"
    })
    .then(res => {
      if (!res.ok) throw new Error("Image fetch failed");
      return res.blob();
    })
    .then(blob => {
      objectUrl = URL.createObjectURL(blob);
      if (mounted) setBlobUrl(objectUrl);
    })
    .catch(console.error);

    return () => {
      mounted = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [src, token]);

  if (!blobUrl) return <span style={style}>Loading…</span>;
  return <img src={blobUrl} alt={alt} style={style} />;
}
