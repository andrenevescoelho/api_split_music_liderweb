# API Local de Split de Música (FastAPI + Docker)

API para separar stems musicais a partir de upload de arquivo de áudio ou URL do YouTube.

## Stack
- Python 3.11
- FastAPI + Uvicorn
- Demucs
- yt-dlp
- ffmpeg
- Docker / docker-compose

## Estrutura

```bash
app/
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

- Defina `API_KEY` no `.env` para **obrigar autenticação** em todos os endpoints de split (`/split/upload`, `/split/youtube`, `/split/result/{job_id}`).
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

### YouTube
- `POST /split/youtube`
- Header opcional/obrigatório (quando configurado): `x-api-key`
- JSON:
```json
{
  "url": "https://www.youtube.com/watch?v=..."
}
```

### Resultado por job
- `GET /split/result/{job_id}`
- Header opcional/obrigatório (quando configurado): `x-api-key`

### Arquivos públicos
- `GET /files/jobs/{job_id}/stems/vocals.mp3`

## Exemplos de curl

### Upload
```bash
curl -X POST "http://localhost:8000/split/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -H "x-api-key: sua-chave" \
  -F "file=@/caminho/musica.mp3"
```

### YouTube
```bash
curl -X POST "http://localhost:8000/split/youtube" \
  -H "accept: application/json" \
  -H "Content-Type: application/json" \
  -H "x-api-key: sua-chave" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
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

## Próximas fases

### Fase 2
- processamento assíncrono
- status por job
- limpeza automática

### Fase 3
- Google Cloud Storage
- signed URLs
- worker/queue em ambiente GCP
