"""Operator-only PostgreSQL 16 backup/restore helper for the production config.
No AWS APIs. Never prints credentials. Restore refuses a nonempty public schema.
"""
import argparse,json,os,subprocess,tempfile
from pathlib import Path
from urllib.parse import urlparse

def main():
 parser=argparse.ArgumentParser();parser.add_argument('action',choices=['backup','restore']);parser.add_argument('file',type=Path);parser.add_argument('--env-file',default='.env.production');args=parser.parse_args()
 config=json.loads(subprocess.check_output(['docker','compose','--env-file',args.env_file,'-f','compose.production.yaml','config','--format','json'],stderr=subprocess.PIPE))
 env=config['services']['backend']['environment'];url=urlparse(env['DB_URL'].removeprefix('jdbc:'));assert url.scheme=='postgresql' and 'sslmode=verify-full' in url.query
 cert=Path('deploy/certs/global-bundle.pem').resolve();assert cert.is_file(),'Download the public RDS CA bundle first'
 values=dict(PGHOST=url.hostname,PGPORT=str(url.port or 5432),PGDATABASE=url.path.lstrip('/'),PGUSER=env['DB_USER'],PGPASSWORD=env['DB_PASSWORD'],PGSSLMODE='verify-full',PGSSLROOTCERT='/certs/global-bundle.pem')
 Path('.runtime').mkdir(exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='db-client-',dir='.runtime') as temporary:
  private=Path(temporary)/'client.env';private.write_text(''.join(k+'='+v+'\n' for k,v in values.items()));private.chmod(0o600)
  command=['docker','run','--rm','-i','--env-file',str(private.resolve()),'--mount','type=bind,src='+str(cert)+',dst=/certs/global-bundle.pem,readonly','postgres:16-alpine']
  if args.action=='backup':
   fd=os.open(args.file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
   try:
    with os.fdopen(fd,'wb') as out:subprocess.run(command+['pg_dump','-Fc','--no-owner','--no-privileges'],stdout=out,stderr=subprocess.PIPE,check=True)
   except Exception:
    args.file.unlink(missing_ok=True);raise RuntimeError('Backup failed; incomplete file removed. Check private DB/TLS connectivity.') from None
   print('Backup completed:',args.file)
  else:
   count=subprocess.check_output(command+['psql','-At','-c',"SELECT count(*) FROM pg_tables WHERE schemaname='public'"],stderr=subprocess.PIPE).decode().strip()
   if count!='0':raise RuntimeError('Restore refused: target public schema is not empty. Use a new empty database.')
   with args.file.open('rb') as source:subprocess.run(command+['pg_restore','--no-owner','--no-privileges','--exit-on-error'],stdin=source,stderr=subprocess.PIPE,check=True)
   print('Restore completed. Verify counts, schema history and cloud identities before starting ingestion.')

if __name__=='__main__':
 try:main()
 except subprocess.CalledProcessError:raise SystemExit('Database operation failed; inspect connectivity/permissions privately. No credentials logged.') from None
