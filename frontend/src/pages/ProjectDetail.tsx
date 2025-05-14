/* eslint-disable react-hooks/exhaustive-deps */
import React, { useState, useEffect } from 'react'
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()
  const [tab, setTab] = useState(0)

  /* commentaires */
  const [newComment, setNewComment] = useState('')
  const [editId, setEditId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')

  /* checklist */
  const [checklist, setChecklist] = useState<ISO42001ChecklistItem[]>([])

  /* dialogue évaluation */
  const [dlgOpen, setDlgOpen] = useState(false)
  const [activeItem, setActiveItem] = useState<ISO42001ChecklistItem | null>(null)
  const [activeQ, setActiveQ] = useState<number | null>(null)
  const [formStatus, setFormStatus] = useState<'to-do'|'in-progress'|'in-review'|'done'>('to-do')
  const [formResult, setFormResult] = useState<'not-assessed'|'partially-compliant'|'not-compliant'|'compliant'|'not-applicable'>('not-assessed')
  const [formObs, setFormObs] = useState('')
  const [proofs, setProofs] = useState<ProofLink[]>([])
  const [files, setFiles] = useState<Record<string,File>>({})

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

  /* checklist */
  const fetchChecklist = async () => {
    try {
      const r = await fetch(`http://127.0.0.1:8000/projects/${id}/checklist`, {
        headers: { Authorization: `Bearer ${t}` }
      })
      if (r.status===401){ logout(); return }
      if (!r.ok) throw new Error(`Erreur ${r.status}`)
      const raw = await r.json() as any[]
      const mapped = raw.map(i=>({
        id:String(i.id),
        control_id:i.control_id,
        control_name:i.control_name,
        description:i.description,
        audit_questions:i.audit_questions,
        evidence_required:i.evidence_required,
        statuses:i.statuses ?? Array(i.audit_questions.length).fill(i.status),
        results:i.results ?? Array(i.audit_questions.length).fill(i.result),
        observations:i.observations ?? Array(i.audit_questions.length).fill(i.observation),
      }))
      setChecklist(mapped)
      recalcScores(mapped)
    } catch(e:any){
      setError(e.message)
    }
  }
  useEffect(() => { if(tab===3) fetchChecklist() }, [tab,id,t])

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

  /* proofs */
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

  /* commentaires CRUD */
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
  const missingProof = () => {
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
                              <Typography variant="caption" color="text.secondary" display="block">{c.date}</Typography>
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
                                  <Typography>{c.content}</Typography>
                                  <Box mt={1}>
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
              {tab===2 && project.aiDetails && (
                <Box>
                  <Typography variant="h6" gutterBottom>Détails du modèle IA</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}><Typography><strong>Type :</strong> {project.aiDetails.type}</Typography></Grid>
                    <Grid item xs={6}><Typography><strong>Modèle :</strong> {project.aiDetails.model}</Typography></Grid>
                    <Grid item xs={6}><Typography><strong>Framework :</strong> {project.aiDetails.framework}</Typography></Grid>
                    <Grid item xs={6}><Typography><strong>Dataset :</strong> {project.aiDetails.datasetSize}</Typography></Grid>
                    <Grid item xs={6}><Typography><strong>Features :</strong> {project.aiDetails.featuresCount}</Typography></Grid>
                    <Grid item xs={6}><Typography><strong>Accuracy :</strong> {project.aiDetails.accuracy}%</Typography></Grid>
                    <Grid item xs={6}><Typography><strong>Training time :</strong> {project.aiDetails.trainingTime}</Typography></Grid>
                  </Grid>
                  <Box mt={4}>
                    <PieChart
                      title="Conformité"
                      labels={['OK','Écart']}
                      data={[project.complianceScore,100-project.complianceScore]}
                      height={200}
                    />
                  </Box>
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
            label="Observation"
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