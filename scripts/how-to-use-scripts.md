# How To Use Scripts

## Upload A File To ADLS Gen2 With SAS

1. Create a local `.env` in the project root (already ignored by git) and copy values from `.env.example`.
2. Set your SAS token and keep it local.

### Python

Run:

```bash
python3 scripts/upload_to_adls.py --source ./data/my-local-file.csv --dest my-local-file.csv
```

### PowerShell

Run:

```powershell
pwsh ./scripts/upload-to-adls.ps1 -Source ./data/my-local-file.csv -Dest my-local-file.csv