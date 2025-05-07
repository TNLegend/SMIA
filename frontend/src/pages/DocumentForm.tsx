// src/pages/DocumentForm.tsx
import { useState, useEffect, ChangeEvent } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Container,
  Box,
  Button,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";
import { Save, ArrowLeft, FileText, Upload } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "../context/AuthContext";
import { useAuthFetch } from "../utils/authFetch";
export default function DocumentForm() {
  const { id } = useParams<{ id?: string }>();
  const isNew = !id || id === "new";
  const { token } = useAuth();
  const nav = useNavigate();

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [uploading, setUploading] = useState(false);
  const authFetch = useAuthFetch()

  // Load existing document
  useEffect(() => {
    if (!isNew) {
        authFetch(`http://127.0.0.1:8000/documents/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
        .then((d) => {
          setTitle(d.title);
          setContent(d.content);
        })
        .catch(console.error);
    }
  }, [id, isNew, token]);

  // Create or update
  const save = async () => {
    const url = `http://127.0.0.1:8000/documents/${isNew ? "" : id}`;
    const method = isNew ? "POST" : "PUT";
    try {
      const res = await authFetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ title, content }),
      });
      if (!res.ok) throw new Error(await res.text());
      nav("/documents");
    } catch (err: any) {
      alert("Erreur : " + (err.message || err));
    }
  };

  // PDF import
  const onPdf = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setUploading(true);
    const res = await authFetch("http://127.0.0.1:8000/documents/upload-pdf", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    setUploading(false);
    if (!res.ok) return alert("Upload failed: " + (await res.text()));
    const d = await res.json();
    nav(`/documents/${d.id}`);
  };

  // New: upload image to the DB & insert markdown link
  const onImg = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || isNew) return;            // must have a saved document first
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    const res = await authFetch(
      `http://127.0.0.1:8000/documents/${id}/images`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      }
    );
    setUploading(false);
    if (!res.ok) {
      return alert("Image upload failed: " + (await res.text()));
    }
    const { id: imgId } = await res.json();
    // Insert standard Markdown reference to protected URL:
    setContent((c) =>
      c + `\n\n![${file.name}](/documents/${id}/images/${imgId})\n\n`
    );
  };

  return (
    <Container maxWidth="md" sx={{ py: 4, position: "relative" }}>
      {(uploading) && (
        <Box
          sx={{
            position: "absolute",
            inset: 0,
            bgcolor: "rgba(0,0,0,0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 10,
          }}
        >
          <CircularProgress color="inherit" />
        </Box>
      )}

      {/* Header */}
      <Box display="flex" alignItems="center" mb={3}>
        <Button
          startIcon={<ArrowLeft size={18} />}
          onClick={() => nav("/documents")}
        >
          Retour
        </Button>
        <Typography variant="h4" ml={2}>
          {isNew ? "Nouveau document" : "Modifier le document"}
        </Typography>
      </Box>

      {/* PDF import */}
      {isNew && (
        <Button
          variant="outlined"
          component="label"
          startIcon={<Upload size={16} />}
          sx={{ mb: 2 }}
        >
          Importer un PDF…
          <input
            type="file"
            hidden
            accept="application/pdf"
            onChange={onPdf}
          />
        </Button>
      )}

      {/* Form */}
      <Box display="flex" flexDirection="column" gap={3}>
        <TextField
          label="Titre"
          fullWidth
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />

        <TextField
          label="Contenu (Markdown)"
          fullWidth
          multiline
          rows={12}
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />

        {/* Image upload */}
        {!isNew && (
          <Button
            variant="outlined"
            component="label"
            startIcon={<FileText size={16} />}
          >
            Ajouter une image…
            <input
              type="file"
              hidden
              accept="image/*"
              onChange={onImg}
            />
          </Button>
        )}

        {/* Preview */}
        <Typography variant="subtitle2">Aperçu :</Typography>
        <Box
          sx={{
            border: "1px solid",
            borderColor: "divider",
            borderRadius: 1,
            p: 2,
            maxHeight: 300,
            overflow: "auto",
          }}
        >
          <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>
            {content}
          </ReactMarkdown>
        </Box>

        {/* Save */}
        <Button
          variant="contained"
          size="large"
          startIcon={<Save size={18} />}
          onClick={save}
        >
          Enregistrer
        </Button>
      </Box>
    </Container>
  );
}
