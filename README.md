# API Local de Split de Música (FastAPI + Docker)

API para separar stems musicais a partir de upload de arquivo de áudio.

## Stack
- Python 3.11
- FastAPI + Uvicorn
- Demucs
- ffmpeg
- librosa (DSP/MIR para BPM, key/mode e tuning)
- Docker / docker-compose

## Estrutura

```bash
app/
  analysis/
  main.py
  core/
  routes/
  schemas/
  services/
  utils/
storage/
  jobs/
  tmp/
Dockerfile
docker-compose.yml
.env.example
requirements.txt
```

## Como rodar localmente

1. Copie o env:
```bash
cp .env.example .env
```

2. Suba a aplicação:
```bash
docker compose up --build
```

3. Swagger:
- http://localhost:8000/docs

## Autenticação

A API suporta autenticação via header `x-api-key`.

- Defina `API_KEY` no `.env` para **obrigar autenticação** em todos os endpoints de split (`/split/upload`, `/split/result/{job_id}`).
- Se `API_KEY` estiver vazio, as rotas funcionam sem autenticação.

Exemplo de header:

```bash
-H "x-api-key: sua-chave"
```

## Endpoints

### Healthcheck
- `GET /health`

### Upload
- `POST /split/upload`
- `multipart/form-data` com `file`
- Header opcional/obrigatório (quando configurado): `x-api-key`

### Resultado por job
- `GET /split/result/{job_id}`
- Header opcional/obrigatório (quando configurado): `x-api-key`

### Arquivos públicos
- `GET /files/jobs/{job_id}/stems/vocals.mp3`

## Pipeline de processamento

1. Converte o áudio de entrada para WAV interno.
2. Executa split via Demucs.
3. Converte stems para MP3.
4. Executa análise musical DSP/MIR (sem LLM):
   - BPM (priorizando stem `drums`, com fallback para mix)
   - Key + mode (priorizando stem `other`, com fallback para mix)
   - Tuning estimado em Hz
5. Retorna split + análise no mesmo payload.

> Se a análise falhar, o split continua sendo retornado normalmente.

## Exemplos de curl

### Upload
```bash
curl -X POST "http://localhost:8000/split/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -H "x-api-key: sua-chave" \
  -F "file=@/caminho/musica.mp3"
```

### Resultado
```bash
curl "http://localhost:8000/split/result/<job_id>" \
  -H "x-api-key: sua-chave"
```

## Exemplo de retorno

```json
{
  "success": true,
  "status": "completed",
  "job_id": "abc123",
  "source_type": "upload",
  "original_audio_url": "http://localhost:8000/files/jobs/abc123/original.mp3",
  "stems": {
    "vocals": "http://localhost:8000/files/jobs/abc123/stems/vocals.mp3",
    "drums": "http://localhost:8000/files/jobs/abc123/stems/drums.mp3",
    "bass": "http://localhost:8000/files/jobs/abc123/stems/bass.mp3",
    "other": "http://localhost:8000/files/jobs/abc123/stems/other.mp3"
  },
  "metadata": {
    "filename": "musica.mp3",
    "duration_seconds": 245,
    "processing_time_seconds": 42
  },
  "analysis": {
    "bpm": 154,
    "displayBpm": 77,
    "key": "D",
    "mode": "major",
    "tuningHz": 440.3,
    "confidence": {
      "bpm": 0.91,
      "key": 0.84
    },
    "sources": {
      "bpm": "drums",
      "key": "other"
    }
  }
}
```

## Erros padronizados

```json
{
  "success": false,
  "error": {
    "code": "INVALID_FILE",
    "message": "Formato de arquivo não suportado."
  }
}
```

## Arquitetura preparada para evolução

- Interface de armazenamento: `StorageService`
- Implementação local: `LocalStorageService`
- Placeholder para GCP: `GCSStorageService`
- Análise musical modular:
  - `app/analysis/bpm_analyzer.py`
  - `app/analysis/key_analyzer.py`
  - `app/analysis/tuning_analyzer.py`
  - `app/analysis/music_analyzer.py`
