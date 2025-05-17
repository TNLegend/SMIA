/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect, useCallback } from 'react'
import { useParams, Link as RouterLink, useNavigate } from 'react-router-dom'
import {
  Box,
  Breadcrumbs,
  Link,
  Typography,
  Button,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Card,
  CardContent,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TableContainer,
  Divider,
  Avatar,
  Tabs,
  Tab,
  TextField,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
} from '@mui/material'
import {
  Home,
  ArrowLeft,
  Download,
  Edit,
  Calendar,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Clock,
} from 'lucide-react'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import PieChart from '../components/charts/PieChart'
import { useAuth } from '../context/AuthContext'
import { useAuthFetch } from '../utils/authFetch';
import { useDropzone, type FileRejection, type DropzoneOptions } from 'react-dropzone';
import { EventSourcePolyfill } from 'event-source-polyfill';

// -------------------------- DropArea util --------------------------
interface DropAreaProps {
  onDrop: (accepted: File[], rej: FileRejection[]) => void;
  accept: DropzoneOptions['accept'];
  placeholder: string;
  multiple?: boolean;
}
const dropStyle = {
  p: 4,
  border: '2px dashed',
  borderColor: 'divider',
  textAlign: 'center',
  cursor: 'pointer',
};
function DropArea({ onDrop, accept, placeholder, multiple = false }: DropAreaProps) {
  const { getRootProps, getInputProps, fileRejections, acceptedFiles } =
    useDropzone({ onDrop, accept, multiple });
  return (
    <>
      <Box {...getRootProps()} sx={dropStyle}>
        <input {...getInputProps()} />
        <Typography>{placeholder}</Typography>
      </Box>
      {fileRejections.length > 0 && (
        <Typography color="error" sx={{ mt: 1 }}>
          Type de fichier non accepté.
        </Typography>
      )}
      {acceptedFiles.length > 0 && (
        <Typography sx={{ mt: 1 }}>
          Fichier sélectionné : {acceptedFiles[0].name}
        </Typography>
      )}
    </>
  );
}
/* Traductions */
const STATUS_LABELS: Record<string, string> = {
  'to-do': 'À faire',
  'in-progress': 'En cours',
  'in-review': 'En révision',
  'done': 'Terminé',
}

const RESULT_LABELS: Record<string, string> = {
  'not-assessed': 'Non évalué',
  'partially-compliant': 'Partiellement conforme',
  'not-compliant': 'Non conforme',
  'compliant': 'Conforme',
  'not-applicable': 'Non applicable',
}

/* utilitaire téléchargement protégé */
function downloadWithAuth(url: string, token: string, filename = 'evidence') {
  return async () => {
    try {
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (res.status === 401) {
        alert('Session expirée, veuillez vous reconnecter.')
        return
      }
      if (res.status === 404) {
        alert('Fichier introuvable.')
        return
      }
      if (!res.ok) throw new Error(`Erreur ${res.status}`)
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(a.href)
    } catch (e: any) {
      alert(e.message)
    }
  }
}

/* types */
interface Phase { name: string; status: 'pending'|'in-progress'|'completed'; date: string }
interface Risk { id: string; category: string; description: string; level: 'low'|'medium'|'high'; impact: number; probability: number; status: string; date: string }
interface AuditQuestion { question: string; evidence_refs: string[] }
interface EvidenceRequired { id: string; description: string }
interface ISO42001ChecklistItem {
  id: string
  control_id: string
  control_name: string
  description: string
  audit_questions: AuditQuestion[]
  evidence_required: EvidenceRequired[]
  statuses: ('to-do'|'in-progress'|'in-review'|'done')[]
  results: ('not-assessed'|'partially-compliant'|'not-compliant'|'compliant'|'not-applicable')[]
  observations: (string|null)[]
}
interface ProofLink { proof_id: number; evidence_id: string; filename: string; download_url: string }
interface Comment { id: string; author: string; date: string; content: string }
interface AIData { type: string; model: string; framework: string; datasetSize: string; featuresCount: number; accuracy: number; trainingTime: string }
interface ProjectDetailAPI {
  id: string
  title: string
  description: string
  category: string
  owner: string
  created: string
  updated: string
  status: 'draft'|'active'|'completed'|'on-hold'
  riskLevel: 'low'|'medium'|'high'
  complianceScore: number
  progress: number
  domain: string
  tags: string[]
  phases?: Phase[]
  team?: { name: string; role: string; avatar: string }[]
  risks?: Risk[]
  comments?: Comment[]
  aiDetails: AIData | null
}

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { token, logout } = useAuth()
  const authFetch = useAuthFetch();
  if (!token) { logout(); return null }
  const t = token

  // couleurs pour status / result
  const statusColorMap: Record<string, 'default'|'info'|'warning'|'success'> = {
    'to-do':'default','in-progress':'info','in-review':'warning','done':'success'
  }
  const resultColorMap: Record<string, 'default'|'warning'|'error'|'success'> = {
    'not-assessed':'default','partially-compliant':'warning','not-compliant':'error','compliant':'success','not-applicable':'default'
  }

  /* état principal */
  const [project, setProject] = useState<ProjectDetailAPI | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string>()
  
  const [tab, setTab] = useState(0)

  /* commentaires */
  const [newComment, setNewComment] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const refreshComments = async () => {
    try {
      const r = await fetch(`http://127.0.0.1:8000/projects/${id}/comments`, {
        headers:{ Authorization:`Bearer ${t}` }
      })
      if(r.status===401){ logout(); return }
      if(!r.ok) throw new Error()
      const data:Comment[] = await r.json()
      setProject(p=>p && ({...p, comments:data}))
    } catch{}
  }

  /* checklist */
  const [checklist, setChecklist] = useState<ISO42001ChecklistItem[]>([])
  const recalcScores = (list: ISO42001ChecklistItem[]) => {
    const total = list.reduce((s,i)=>s + i.audit_questions.length,0)
    const done  = list.reduce((s,i)=>s + i.statuses.filter(x=>x==='done').length,0)
    const comp  = list.reduce((s,i)=>s + i.results.filter(x=>x==='compliant').length,0)
    setProject(p=>p && ({
      ...p,
      progress: Math.round(done/total*100),
      complianceScore: Math.round(comp/total*100)
    }))
  }

 const fetchChecklist = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch(`http://127.0.0.1:8000/projects/${id}/checklist`, {
        headers: { Authorization: `Bearer ${t}` }
      })

      if (res.status === 401) {
        logout()
        return
      }
      if (!res.ok) {
        throw new Error(`Impossible de charger la checklist (code ${res.status})`)
      }

      const raw = await res.json() as any[]
      const mapped = raw.map(i => ({
        id: String(i.id),
        control_id: i.control_id,
        control_name: i.control_name,
        description: i.description,
        audit_questions: i.audit_questions,
        evidence_required: i.evidence_required,
        statuses: i.statuses ?? Array(i.audit_questions.length).fill(i.status),
        results: i.results ?? Array(i.audit_questions.length).fill(i.result),
        observations: i.observations ?? Array(i.audit_questions.length).fill(i.observation),
      }))

      setChecklist(mapped)
      recalcScores(mapped)
    } catch (e: any) {
      setError(e.message || 'Erreur inconnue lors du chargement de la checklist')
    } finally {
      setLoading(false)
    }
  }, [id, t, logout, recalcScores])

  useEffect(() => { if(tab===3) fetchChecklist() }, [tab,id,t])

useEffect(() => {
if (project) return
refreshComments()
}, [project])

  /* dialogue évaluation */
  const [dlgOpen, setDlgOpen] = useState(false)
  const [activeItem, setActiveItem] = useState<ISO42001ChecklistItem | null>(null)
  const [activeQ, setActiveQ] = useState<number | null>(null)
  const [formStatus, setFormStatus] = useState<'to-do'|'in-progress'|'in-review'|'done'>('to-do')
  const [formResult, setFormResult] = useState<'not-assessed'|'partially-compliant'|'not-compliant'|'compliant'|'not-applicable'>('not-assessed')
  const [formObs, setFormObs] = useState('')
  const [proofs, setProofs] = useState<ProofLink[]>([])
  const [files, setFiles] = useState<Record<string,File>>({})
    async function loadProofs(itemId:string, qIdx:number){
    try {
      const r = await fetch(
        `http://127.0.0.1:8000/projects/${id}/checklist/${itemId}/questions/${qIdx}/proofs`,
        { headers:{ Authorization:`Bearer ${t}` } }
      )
      if(r.status===401){ logout(); return }
      if(!r.ok){ setProofs([]); return }
      setProofs(await r.json())
    } catch{
      setProofs([])
    }
  }

  // Stepper state
  const steps = [
    'Importer le modèle',
    'Dataset entraînement',
    'Features / Target',
    'Config YAML',
    'Entraînement',
    'Dataset test',
    'Évaluation'
  ];
  const [activeStep, setActiveStep] = useState(0);

  const isStepReady = (step: number): boolean => {
    switch (step) {
      case 0:
        return modelFiles.length > 0;
      case 1:
        return trainDatasetId !== null && datasetColumns.length > 0;
      case 2:
        return !!selectedTarget && selectedFeatures.length > 0;
      case 3:
        return true;              // rien à valider de plus ici
      case 4:
        return trainingFinished;
      case 5:
        return testDatasetColumns.length > 0;
      case 6:
        return evalFinished;
      default:
        return false;
    }
  };

  /** handlers globaux afin de ne pas dupliquer */
  const handleNext = () => setActiveStep((s) => (s < steps.length - 1 ? s + 1 : s));
  const handleBack = () => setActiveStep((s) => (s > 0 ? s - 1 : s));

  /* Model files upload */
  const [modelFiles, setModelFiles] = useState<string[]>([]);
  const [zipError, setZipError] = useState<string>();
  const onDrop = async (
  acceptedFiles: File[],
  fileRejections: FileRejection[]
) => {
  /* 1) Rejet immédiat par Dropzone */
  if (fileRejections.length > 0) {
    setZipError('Seuls les fichiers .zip sont acceptés.')
    return
  }

  /* 2) Fichier retenu */
  const file = acceptedFiles[0]
  if (!file) return

  /* 3) Double-check de l’extension */
  if (!file.name.toLowerCase().endsWith('.zip')) {
    setZipError('Seuls les fichiers .zip sont acceptés.')
    return
  }

  setZipError(undefined)
  setLoading(true)

  /* 4) Prépare un FormData → champ « zip_file » */
  const form = new FormData()
  form.append('zip_file', file, file.name) // <-- le nom du champ DOIT être zip_file

  try {
    /* ───── 1. Vérification du template ───── */
    let res = await authFetch(
      `http://127.0.0.1:8000/projects/${id}/model/template/check`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }, // on NE fixe PAS Content-Type
        body: form,
      }
    )

    const checkJson = await res.json()
    if (!checkJson.ok) {
      setZipError(
        `Fichiers manquants : ${checkJson.missing_files.join(
          ', '
        )} ; fonction(s) manquante(s) : ${checkJson.missing_functions.join(', ')}`
      )
      return
    }

    /* ───── 2. Upload définitif ───── */
    res = await authFetch(
      `http://127.0.0.1:8000/projects/${id}/model/upload_model`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form, // on ré-envoie exactement le même FormData
      }
    )

    const uploadJson = await res.json()
    if (!res.ok) throw new Error(uploadJson.detail || 'Erreur upload')
    setModelFiles(uploadJson.files)
  } catch (err: any) {
    setZipError(err.message)
  } finally {
    setLoading(false)
  }
}
  /* Dataset train upload */
  const [datasetColumns, setDatasetColumns] = useState<string[]>([])
  const [trainDatasetId, setTrainDatasetId] = useState<number | null>(null)
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
const [selectedTarget, setSelectedTarget]     = useState<string | null>(null);
const [selectedSensitive, setSelectedSensitive] = useState<string[]>([]);
const [configYAML, setConfigYAML]     = useState<string>('')
const [configError, setConfigError]   = useState<string>('')
// ─── Step 5: entraînement ───
const [runId, setRunId] = useState<number | null>(null);
const [trainingLogs, setTrainingLogs] = useState<string[]>([]);
const [trainingLoading, setTrainingLoading] = useState(false);
const [trainingFinished, setTrainingFinished] = useState(false);
const [testDatasetId, setTestDatasetId] = useState<number | null>(null)
const [testDatasetColumns, setTestDatasetColumns] = useState<string[]>([])
const [evalRunId, setEvalRunId] = useState<number | null>(null)
const [evalLogs, setEvalLogs] = useState<string[]>([])
const [evalLoading, setEvalLoading] = useState(false)
const [evalFinished, setEvalFinished] = useState(false)
const startEval=async()=>{
    setEvalLoading(true);
    try{
      const res=await authFetch(`/projects/${id}/evaluate`,{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${t}`},body:JSON.stringify({model_run_id:runId,test_data_id:testDatasetId,data_config_id:trainDatasetId})});
      const json=await res.json(); setEvalRunId(json.eval_id);
      // SSE for eval logs
      const src=new EventSourcePolyfill(`/projects/${id}/evaluate/${json.eval_id}/stream`,{headers:{Authorization:`Bearer ${t}`}});
      src.onmessage=e=>{ setEvalLogs(l=>[...l,e.data]); if(e.data.startsWith('Evaluation finished')){ setEvalFinished(true); src.close(); }};
      src.onerror=()=>src.close();
    }catch(e:any){alert(e.message);}finally{setEvalLoading(false);}  };


// Nouveau handler pour l’étape 2
const onDropDataset = async (
  acceptedFiles: File[],
  fileRejections: FileRejection[]
) => {
  if (fileRejections.length > 0) {
    setZipError('Seuls les fichiers .csv sont acceptés.')
    return
  }
  const file = acceptedFiles[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv')) {
    setZipError('Seuls les fichiers .csv sont acceptés.')
    return
  }

  setZipError(undefined)
  setLoading(true)
  const form = new FormData()
  form.append('file', file, file.name) // 👉 le champ 'file' côté back

  try {
    const res = await authFetch(
      `http://127.0.0.1:8000/projects/${id}/model/upload_dataset?kind=train`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      }
    )
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || 'Erreur upload dataset')
    }
    const json = await res.json() as { dataset_id: number; columns: string[] }
    setTrainDatasetId(json.dataset_id)
    setDatasetColumns(json.columns)
  } catch (e: any) {
    setZipError(e.message)
  } finally {
    setLoading(false)
  }
}


const onDropTestDataset = async (
  acceptedFiles: File[],
  fileRejections: FileRejection[]
) => {
  if (fileRejections.length > 0) {
    setZipError('Seuls les fichiers .csv sont acceptés.')
    return
  }
  const file = acceptedFiles[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.csv')) {
    setZipError('Seuls les fichiers .csv sont acceptés.')
    return
  }

  setZipError(undefined)
  setLoading(true)
  const form = new FormData()
  form.append('file', file, file.name) // 👉 le champ 'file' côté back

  try {
    const res = await authFetch(
      `http://127.0.0.1:8000/projects/${id}/model/upload_dataset?kind=test`,
      {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: form,
      }
    )
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail || 'Erreur upload dataset')
    }
    const json = await res.json() as { dataset_id: number; columns: string[] }
    setTestDatasetId(json.dataset_id)
    setTestDatasetColumns(json.columns)
  } catch (e: any) {
    setZipError(e.message)
  } finally {
    setLoading(false)
  }
}

const startTraining = async () => {
  setTrainingLoading(true);
  try {
    const res = await authFetch(
      `http://127.0.0.1:8000/projects/${id}/model/train`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: trainDatasetId }),
      }
    );
    if (!res.ok) throw new Error('Impossible de démarrer');
    const { run_id } = await res.json() as { run_id: number };
    setRunId(run_id);
  } catch (e: any) {
    alert(e.message);
  } finally {
    setTrainingLoading(false);
  }
};

// Dès qu'on a un runId, on ouvre le stream SSE
useEffect(() => {
  if (!runId) return;
  const src = new EventSourcePolyfill(
    `http://127.0.0.1:8000/projects/${id}/model/runs/${runId}/stream`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  src.onmessage = e => {
    setTrainingLogs(logs => [...logs, e.data]);
    if (e.data.startsWith('Training finished')) {
      setTrainingFinished(true);
      src.close();
    }
  };
  src.onerror = () => { src.close(); };
  return () => { src.close(); };
}, [runId]);


  /* charger projet */
  useEffect(() => {
    fetch(`http://127.0.0.1:8000/projects/${id}`, {
      headers: { Authorization: `Bearer ${t}` }
    })
    .then(async r => {
      if (r.status===401){ logout(); throw new Error('Session expirée') }
      if (!r.ok) throw new Error(`Erreur ${r.status}`)
      return r.json()
    })
    .then(setProject)
    .catch(e=>setError(e.message))
    .finally(()=>setLoading(false))
  }, [id,t,logout])

  
  
  // charger le config.yaml quand on arrive à l'étape 4
  useEffect(() => {
    const loadConfig = async () => {
      try {
        setLoading(true)
        const res = await authFetch(
          `http://127.0.0.1:8000/projects/${id}/model/config`,
          { method: 'GET', headers: { Authorization: `Bearer ${t}` } }
        )
        if (!res.ok) throw new Error(`Erreur ${res.status}`)
        const text = await res.text()
        setConfigYAML(text)
        setConfigError('')
      } catch (e: any) {
        setConfigError(e.message)
      } finally {
        setLoading(false)
      }
    }
    if (activeStep === 3) loadConfig()
  }, [activeStep, id, t])

  

  /* dialog helpers */
  const openDlg = (item:ISO42001ChecklistItem, idx:number) => {
    setActiveItem(item)
    setActiveQ(idx)
    setFormStatus(item.statuses[idx])
    setFormResult(item.results[idx])
    setFormObs(item.observations[idx]||'')
    setFiles({})
    loadProofs(item.id, idx)
    setDlgOpen(true)
  }
  const closeDlg = () => {
    setDlgOpen(false)
    setActiveItem(null)
    setActiveQ(null)
    setProofs([])
    setFiles({})
  }

  const proofExist = (evId:string)=>proofs.find(p=>p.evidence_id===evId)
  const missingProof = (): boolean => {
    if(!activeItem||activeQ===null) return false
    if(formResult!=='compliant') return false
    return activeItem
      .audit_questions[activeQ]
      .evidence_refs
      .some(evId=>!proofExist(evId)&&!files[evId])
  }

  /* save évaluation */
  const saveEval = async () => {
    if(!activeItem||activeQ===null) return
    // upload
    const q = activeItem.audit_questions[activeQ]
    for(const evId of q.evidence_refs){
      const f = files[evId]
      if(f){
        const fd = new FormData()
        fd.append('file', f)
        fd.append('evidence_id', evId)
        await fetch(
          `http://127.0.0.1:8000/projects/${id}/checklist/${activeItem.id}/proofs`,
          {
            method:'POST',
            headers:{ Authorization:`Bearer ${t}` },
            body:fd
          }
        )
      }
    }
    // update
    const payload = {
      status:formStatus,
      result:formResult,
      observation:formObs,
      questionIndex:activeQ
    }
    const r = await fetch(
      `http://127.0.0.1:8000/projects/${id}/checklist/${activeItem.id}`,
      {
        method:'PUT',
        headers:{ 'Content-Type':'application/json', Authorization:`Bearer ${t}` },
        body:JSON.stringify(payload)
      }
    )
    if(r.status===401){ logout(); return }
    if(!r.ok){
      const j = await r.json().catch(()=>({detail:'Erreur'}))
      return alert(j.detail)
    }
    // local update
    const upd = checklist.map(it=>{
      if(it.id!==activeItem.id) return it
      const st=[...it.statuses], rs=[...it.results], ob=[...it.observations]
      st[activeQ]=formStatus; rs[activeQ]=formResult; ob[activeQ]=formObs
      return {...it, statuses:st, results:rs, observations:ob}
    })
    setChecklist(upd)
    recalcScores(upd)
    closeDlg()
  }

  /* rendu */
  if(loading) return <Box textAlign="center" py={4}><CircularProgress/></Box>
  if(error)   return <Typography align="center" color="error" py={4}>{error}</Typography>
  if(!project) return null

  const phases = project.phases ?? []
  const team   = project.team   ?? []
  const risks  = project.risks  ?? []
  const comments = project.comments ?? []

  const riskIcon = (lvl:ProjectDetailAPI['riskLevel']) =>
    lvl==='high'?<ShieldAlert size={16}/>
    :lvl==='medium'?<AlertTriangle size={16}/>
    :<CheckCircle2 size={16}/>


  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb:2 }}>
        <Link component={RouterLink} to="/" sx={{display:'flex',alignItems:'center'}}>
          <Home size={16} style={{marginRight:4}}/> Accueil
        </Link>
        <Link component={RouterLink} to="/projects">Projets</Link>
        <Typography color="text.primary">{project.title}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center">
          <Button component={RouterLink} to="/projects" variant="outlined" startIcon={<ArrowLeft size={18}/>}>
            Retour
          </Button>
          <Typography variant="h4" sx={{ml:2}}>{project.title}</Typography>
        </Box>
        <Box>
          <Button startIcon={<Download size={18}/>}>Exporter</Button>
          <Button startIcon={<Edit size={18}/>} variant="contained" sx={{ml:1}} onClick={()=>navigate(`/projects/${id}/edit`)}>
            Modifier
          </Button>
        </Box>
      </Box>

      {/* Tags */}
      <Box display="flex" flexWrap="wrap" gap={1} mb={3}>
        <Chip label={project.category} size="small" color="primary"/>
        <Chip label={project.status} size="small"/>
        <Chip icon={riskIcon(project.riskLevel)} label={`Risque ${project.riskLevel}`} size="small"/>
        <Chip label={`Conformité ${project.complianceScore}%`} size="small"/>
      </Box>

      <Grid container spacing={3}>
        {/* MAIN */}
        <Grid item xs={12} md={8}>
          {/* Description */}
          <Card sx={{mb:3}}><CardContent>
            <Typography variant="h6">Description</Typography>
            <Typography paragraph>{project.description}</Typography>
            <Typography variant="subtitle1">Progression</Typography>
            <Box display="flex" alignItems="center">
              <Box flexGrow={1} mr={2}>
                <LinearProgress variant="determinate" value={project.progress}/>
              </Box>
              <Typography>{project.progress}%</Typography>
            </Box>
          </CardContent></Card>

          {/* Phases */}
          <Card sx={{mb:3}}><CardContent>
            <Typography variant="h6">Phases du projet</Typography>
            <Stepper orientation="vertical">
              {phases.map((ph,i)=>(
                <Step key={i} active={ph.status!=='pending'} completed={ph.status==='completed'}>
                  <StepLabel icon={
                    ph.status==='completed'?<CheckCircle2 size={20} color="success"/>
                    :ph.status==='in-progress'?<Activity size={20}/>
                    :<Clock size={20}/>
                  }>
                    <Box>
                      <Typography sx={{fontWeight:ph.status==='pending'?'regular':'medium'}}>{ph.name}</Typography>
                      <Typography variant="caption" color="text.secondary" display="flex" alignItems="center">
                        <Calendar size={14} style={{marginRight:4}}/> {ph.date}
                      </Typography>
                    </Box>
                  </StepLabel>
                </Step>
              ))}
            </Stepper>
          </CardContent></Card>

          {/* Tabs */}
          <Card>
            <Tabs value={tab} onChange={(_,v)=>setTab(v)}>
              <Tab label="Risques"/><Tab label="Commentaires"/><Tab label="Détails IA"/><Tab label="Audit"/><Tab label="Historique"/>
            </Tabs>
            <Divider/>
            <CardContent>
              {/* 0 — Risques */}
              {tab===0 && (
                <TableContainer>
                  <Table size="small">
                    <TableHead><TableRow>
                      <TableCell>Niveau</TableCell><TableCell>Catégorie</TableCell><TableCell>Description</TableCell>
                      <TableCell>Impact</TableCell><TableCell>Probabilité</TableCell><TableCell>Statut</TableCell><TableCell>Date</TableCell>
                    </TableRow></TableHead>
                    <TableBody>
                      {risks.map(r=>(
                        <TableRow key={r.id}>
                          <TableCell>
                            <Chip icon={
                              r.level==='high'?<ShieldAlert size={16}/>
                              :r.level==='medium'?<AlertTriangle size={16}/>
                              :<CheckCircle2 size={16}/>
                            } label={r.level} size="small"/>
                          </TableCell>
                          <TableCell>{r.category}</TableCell>
                          <TableCell>{r.description}</TableCell>
                          <TableCell>{r.impact}</TableCell>
                          <TableCell>{r.probability}</TableCell>
                          <TableCell>{r.status}</TableCell>
                          <TableCell>{r.date}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}

              {/* 1 — Commentaires */}
              {tab===1 && (
                <>
                  <Box mb={2}>
                    <TextField label="Ajouter un commentaire" multiline rows={3} fullWidth value={newComment} onChange={e=>setNewComment(e.target.value)}/>
                    <Box textAlign="right" mt={1}>
                      <Button variant="contained" onClick={async()=>{
                        if(!newComment.trim())return
                        const r = await fetch(`http://127.0.0.1:8000/projects/${id}/comments`,{
                          method:'POST',
                          headers:{ 'Content-Type':'application/json', Authorization:`Bearer ${t}` },
                          body:JSON.stringify({content:newComment})
                        })
                        if(r.status===401){ logout(); return }
                        if(!r.ok) return alert('Erreur')
                        setNewComment('')
                        refreshComments()
                      }}>Publier</Button>
                    </Box>
                  </Box>
                  <Divider sx={{my:2}}/>
                  <List>
                    {comments.map(c=>(
                      <ListItem key={c.id} alignItems="flex-start">
                        <ListItemAvatar><Avatar>{c.author[0]}</Avatar></ListItemAvatar>
                        <ListItemText
                          primary={c.author}
                          secondary={
                            <>
                              <Typography variant="caption" color="text.secondary" display="block" component="span" >{c.date}</Typography>
                              {editId===c.id ? (
                                <>
                                  <TextField fullWidth multiline value={editContent} onChange={e=>setEditContent(e.target.value)}/>
                                  <Box mt={1}>
                                    <Button size="small" variant="contained" onClick={async()=>{
                                      const r = await fetch(`http://127.0.0.1:8000/projects/${id}/comments/${c.id}`,{
                                        method:'PUT',
                                        headers:{ 'Content-Type':'application/json', Authorization:`Bearer ${t}` },
                                        body:JSON.stringify({content:editContent})
                                      })
                                      if(r.status===401){ logout(); return }
                                      if(!r.ok) return alert('Erreur')
                                      setEditId(null); setEditContent('')
                                      refreshComments()
                                    }}>Sauvegarder</Button>
                                    <Button size="small" sx={{ml:1}} onClick={()=>setEditId(null)}>Annuler</Button>
                                  </Box>
                                </>
                              ) : (
                                <>
                                  <Typography component="span">{c.content}</Typography>
                                  <Box component="span" mt={1}>
                                    <Button size="small" onClick={()=>{ setEditId(c.id); setEditContent(c.content) }}>Modifier</Button>
                                    <Button size="small" color="error" onClick={async()=>{
                                      if(!window.confirm('Supprimer ?'))return
                                      const r = await fetch(`http://127.0.0.1:8000/projects/${id}/comments/${c.id}`,{
                                        method:'DELETE',
                                        headers:{ Authorization:`Bearer ${t}` }
                                      })
                                      if(r.status===401){ logout(); return }
                                      if(!r.ok) return alert('Erreur')
                                      refreshComments()
                                    }}>Supprimer</Button>
                                  </Box>
                                </>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </>
              )}

              {/* 2 — Détails IA */}
{/* 2 — Détails IA */}
{tab === 2 && (
  <Box>
    {/* Stepper en haut de l’onglet Détails IA */}
    <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
            {steps.map((label) => (
              <Step key={label} completed={isStepReady(steps.indexOf(label))}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

    {/* Panel for Étape 1: Importer modèle */}
                  {/* Etape 1: Import modèle */}
                  {activeStep === 0 && (
                    <Card sx={{ mt: 3 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          Étape 1: Importer le modèle (ZIP)
                        </Typography>
                        <Box mb={2}>
                          <Button
                            variant="outlined"
                            startIcon={<Download size={18}/>} 
                            onClick={downloadWithAuth(
                              `http://127.0.0.1:8000/templates/model`, t, 'template.zip'
                            )}
                          >
                            Télécharger le template
                          </Button>
                        </Box>
                        <DropArea
                          onDrop={onDrop}
                          accept={{ 'application/zip': ['.zip'] }}
                          placeholder="Glissez ou cliquez pour ajouter un ZIP"
                        />
                        {zipError && <Typography color="error" sx={{ mt:2 }}>{zipError}</Typography>}

                        {modelFiles.length > 0 && (
                          <Box sx={{ mt:2 }}>
                            <Typography variant="subtitle2">Aperçu des fichiers importés :</Typography>
                            <List dense>
                              {modelFiles.map(fileName => (
                                <ListItem key={fileName}>
                                  <ListItemAvatar>
                                    <Avatar><ArrowLeft size={16}/></Avatar>
                                  </ListItemAvatar>
                                  <ListItemText primary={fileName}/>
                                </ListItem>
                              ))}
                            </List>
                          </Box>
                        )}

                        <Box sx={{ mt:3, display:'flex', justifyContent:'flex-end', gap:2 }}>
                          <Button variant="contained" onClick={handleNext} disabled={!isStepReady(0)}>
                            Suivant
                          </Button>
                        </Box>
                      </CardContent>
                    </Card>
                  )}

                  {/* Etape 2: Dataset entraînement */}
                  {activeStep === 1 && (
                    <Card sx={{ mt:3 }}>
                      <CardContent>
                        <Typography variant="h6">Étape 2: Dataset entraînement (CSV)</Typography>
                        <DropArea
                          onDrop={onDropDataset}
                          accept={{ 'text/csv': ['.csv'] }}
                          placeholder="Glissez ou cliquez pour ajouter un CSV d’entraînement"
                        />
                        {zipError && <Typography color="error" sx={{ mt:2 }}>{zipError}</Typography>}

                        {datasetColumns.length > 0 && (
                          <Box sx={{ mt:3, display:'flex', justifyContent:'space-between' }}>
                            <Button variant="outlined" onClick={handleBack}>Précédent</Button>
                            <Button variant="contained" onClick={handleNext} disabled={!isStepReady(1)}>Suivant</Button>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {/* Etape 3: Features / Target */}
                  {activeStep === 2 && (
                    <Card sx={{ mt:3 }}>
                      <CardContent>
                        <Typography variant="h6">Étape 3: Features / Target / Sensitives</Typography>
                        {/* Autocomplete, Select UI here */}
                        <Box sx={{ mt:3, display:'flex', justifyContent:'space-between' }}>
                          <Button variant="outlined" onClick={handleBack}>Précédent</Button>
                          <Button variant="contained" onClick={handleNext} disabled={!isStepReady(2)}>Suivant</Button>
                        </Box>
                      </CardContent>
                    </Card>
                  )}

                  {/* Etape 4: Config YAML */}
                  {activeStep === 3 && (
                    <Card sx={{ mt:3 }}>
                      <CardContent>
                        <Typography variant="h6">Étape 4: Modifier config.yaml</Typography>
                        {/* TextField YAML */}
                        <Box sx={{ mt:3, display:'flex', justifyContent:'space-between' }}>
                          <Button variant="outlined" onClick={handleBack}>Précédent</Button>
                          <Button variant="contained" onClick={handleNext}>Suivant</Button>
                        </Box>
                      </CardContent>
                    </Card>
                  )}

                  {/* Etape 5: Entraînement */}
                  {activeStep === 4 && (
                    <Card sx={{ mt:3 }}>
                      <CardContent>
                        <Typography variant="h6">Étape 5: Lancement de l’entraînement</Typography>
                        {!runId ? (
                          <Button variant="contained" onClick={startTraining} disabled={trainingLoading || !trainDatasetId} startIcon={trainingLoading ? <CircularProgress size={20}/> : null}>
                            {trainingLoading ? 'Démarrage…' : 'Démarrer'}
                          </Button>
                        ) : (
                          <Box mt={2}>
                            <Typography variant="subtitle2">Logs run #{runId}:</Typography>
                            <List sx={{ maxHeight:300, overflow:'auto', bgcolor:'background.paper', border:'1px solid divider' }}>
                              {trainingLogs.map((l,i)=>(<ListItem key={i} dense><Typography component="pre" variant="body2" sx={{ m:0 }}>{l}</Typography></ListItem>))}
                            </List>
                            {!trainingFinished ? <Typography variant="caption">En cours…</Typography> : <Typography color="success.main">Entraînement terminé ✔</Typography>}
                          </Box>
                        )}
                        <Box sx={{ mt:3, display:'flex', justifyContent:'space-between' }}>
                          <Button variant="outlined" onClick={handleBack}>Précédent</Button>
                          <Button variant="contained" onClick={handleNext} disabled={!isStepReady(4)}>Suivant</Button>
                        </Box>
                      </CardContent>
                    </Card>
                  )}

                  {/* Etape 6: Dataset test */}
                  {activeStep === 5 && (
                    <Card sx={{ mt:3 }}>
                      <CardContent>
                        <Typography variant="h6">Étape 6: Dataset test (CSV)</Typography>
                        <DropArea onDrop={onDropTestDataset} accept={{ 'text/csv':['.csv'] }} placeholder="Glissez ou cliquez pour ajouter un CSV test"/>
                        {testDatasetColumns.length>0 && (
                          <Box sx={{ mt:2, display:'flex', justifyContent:'space-between' }}>
                            <Button variant="outlined" onClick={handleBack}>Précédent</Button>
                            <Button variant="contained" onClick={handleNext} disabled={!isStepReady(5)}>Suivant</Button>
                          </Box>
                        )}
                      </CardContent>
                    </Card>
                  )}

                  {/* Etape 7: Évaluation */}
                  {activeStep === 6 && (
                    <Card sx={{ mt:3 }}>
                      <CardContent>
                        <Typography variant="h6">Étape 7: Lancer l’évaluation</Typography>
                        {!evalRunId ? (
                          <Button variant="contained" onClick={startEval} disabled={!runId||!testDatasetId||evalLoading}>
                            {evalLoading?'Démarrage…':'Lancer'}
                          </Button>
                        ) : (
                          <Box mt={2}>
                            <Typography>Logs évaluation #{evalRunId}:</Typography>
                            <List sx={{ maxHeight:300, overflow:'auto', bgcolor:'#fafafa', border:'1px solid #ddd' }}>
                              {evalLogs.map((l,i)=>(<ListItem key={i}><Typography component="pre" variant="body2">{l}</Typography></ListItem>))}
                            </List>
                            {evalFinished ? <Typography color="success.main">Évaluation terminée ✔</Typography> : <Typography variant="caption">En cours…</Typography>}
                          </Box>
                        )}
                        <Box sx={{ mt:3, display:'flex', justifyContent:'flex-start' }}>
                          <Button variant="outlined" onClick={handleBack}>Précédent</Button>
                        </Box>
                      </CardContent>
                    </Card>
                  )}


    {/* --- affichage des détails IA uniquement si un modèle a déjà été importé --- */}
    {project.aiDetails && (
      <>
        <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
          Détails du modèle IA
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography>
              <strong>Type :</strong> {project.aiDetails.type}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography>
              <strong>Modèle :</strong> {project.aiDetails.model}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography>
              <strong>Framework :</strong> {project.aiDetails.framework}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography>
              <strong>Dataset :</strong> {project.aiDetails.datasetSize}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography>
              <strong>Features :</strong> {project.aiDetails.featuresCount}
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography>
              <strong>Accuracy :</strong> {project.aiDetails.accuracy}%
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography>
              <strong>Training time :</strong> {project.aiDetails.trainingTime}
            </Typography>
          </Grid>
        </Grid>
        <Box mt={4}>
          <PieChart
            title="Conformité"
            labels={['OK', 'Écart']}
            data={[project.complianceScore, 100 - project.complianceScore]}
            height={200}
          />
        </Box>
      </>
    )}
  </Box>
)}
    
              {/* 3 — Audit */}
              {tab===3 && (
                <Box>
                  {checklist.map(item=>(
                    <Accordion key={item.id} sx={{mb:1}}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon/>}>
                        <Box sx={{flexGrow:1}}>
                          <Typography variant="subtitle1">{item.control_name}</Typography>
                          <Typography variant="caption" color="text.secondary">{item.description}</Typography>
                        </Box>
                        <Chip label={`${item.statuses.filter(s=>'done'===s).length}/${item.audit_questions.length}`} size="small" sx={{ml:1}}/>
                      </AccordionSummary>
                      <AccordionDetails>
                        {item.audit_questions.map((aq,idx)=>(
                          <Box key={idx} display="flex" alignItems="center" mb={2}>
                            <Box flexGrow={1} display="flex" alignItems="center">
                              <Typography>Q{idx+1} : {aq.question}</Typography>
                              <Chip
                                label={STATUS_LABELS[item.statuses[idx]]}
                                color={statusColorMap[item.statuses[idx]]}
                                size="small"
                                sx={{ml:2,mr:1}}
                              />
                              <Chip
                                label={RESULT_LABELS[item.results[idx]]}
                                color={resultColorMap[item.results[idx]]}
                                size="small"
                              />
                            </Box>
                            <Button size="small" onClick={()=>openDlg(item,idx)}>Évaluer</Button>
                          </Box>
                        ))}
                      </AccordionDetails>
                    </Accordion>
                  ))}
                </Box>
              )}

              {/* 4 — Historique */}
              {tab===4 && <Typography>Pas encore d’historique.</Typography>}
            </CardContent>
          </Card>
        </Grid>

        {/* SIDEBAR */}
        <Grid item xs={12} md={4}>
          <Card sx={{mb:3}}><CardContent>
            <Typography variant="h6" gutterBottom>Informations</Typography>
            <Typography><strong>Responsable :</strong> {project.owner}</Typography>
            <Typography><strong>Créé le :</strong> {project.created}</Typography>
            <Typography><strong>MàJ :</strong> {project.updated}</Typography>
            <Typography><strong>Domaine :</strong> {project.domain}</Typography>
          </CardContent></Card>
          <Card><CardContent>
            <Typography variant="h6" gutterBottom>Équipe</Typography>
            <List>
              {team.map(m=>(
                <ListItem key={m.name}>
                  <ListItemAvatar><Avatar src={m.avatar}>{m.name.charAt(0)}</Avatar></ListItemAvatar>
                  <ListItemText primary={m.name} secondary={m.role}/>
                </ListItem>
              ))}
            </List>
          </CardContent></Card>
        </Grid>
      </Grid>

      {/* Dialogue évaluation */}
      <Dialog open={dlgOpen} onClose={closeDlg} fullWidth maxWidth="sm">
        <DialogTitle>
          {activeItem?.control_name}
          {activeQ!==null && <> — Q{activeQ+1} : {activeItem!.audit_questions[activeQ].question}</>}
        </DialogTitle>
        <DialogContent>
          <FormControl fullWidth margin="dense">
            <InputLabel>Statut</InputLabel>
            <Select value={formStatus} label="Statut" onChange={e=>setFormStatus(e.target.value as any)}>
              <MenuItem value="to-do">À faire</MenuItem>
              <MenuItem value="in-progress">En cours</MenuItem>
              <MenuItem value="in-review">En révision</MenuItem>
              <MenuItem value="done">Terminé</MenuItem>
            </Select>
          </FormControl>
          <FormControl fullWidth margin="dense">
            <InputLabel>Résultat</InputLabel>
            <Select value={formResult} label="Résultat" onChange={e=>setFormResult(e.target.value as any)}>
              <MenuItem value="not-assessed">Non évalué</MenuItem>
              <MenuItem value="partially-compliant">Partiellement conforme</MenuItem>
              <MenuItem value="not-compliant">Non conforme</MenuItem>
              <MenuItem value="compliant">Conforme</MenuItem>
              <MenuItem value="not-applicable">Non applicable</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            margin="dense"
            label="recommendation"
            multiline
            minRows={3}
            value={formObs}
            onChange={e=>setFormObs(e.target.value)}
          />

          {formResult==='compliant' && activeItem && activeQ!==null && (
            <Box mt={2}>
              <Typography variant="subtitle2">Preuves attendues</Typography>
              {activeItem.audit_questions[activeQ].evidence_refs.map(refId=>{
                const ev = activeItem.evidence_required.find(e=>e.id===refId)
                const exist = proofExist(refId)
                return (
                  <Box key={refId} mb={2}>
                    <Typography>• {ev?.description||refId}</Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      {exist && (
                        <Button
                          size="small"
                          onClick={downloadWithAuth(
                            `http://127.0.0.1:8000/projects/${id}/proofs/${exist.proof_id}`,
                            t,
                            exist.filename
                          )}
                        >
                          Voir preuve existante
                        </Button>
                      )}
                      <Button
                        size="small"
                        onClick={downloadWithAuth(
                          `http://127.0.0.1:8000/projects/${id}/checklist/${activeItem.id}/proofs/template/${refId}`,
                          t,
                          `${refId}.docx`
                        )}
                      >
                        Télécharger preuve vierge
                      </Button>
                    </Box>
                    <input
                      type="file"
                      style={{display:'block',marginTop:8}}
                      onChange={e=>{
                        const f = e.target.files?.[0]
                        if(f) setFiles(p=>({...p,[refId]:f}))
                      }}
                    />
                  </Box>
                )
              })}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDlg}>Annuler</Button>
          <Button variant="contained" onClick={saveEval} disabled={missingProof()}>
            Sauvegarder
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}