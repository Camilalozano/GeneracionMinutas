-- Exclusivo del proyecto zwpmdgpywgypdmqygsvv.
-- Creación aditiva: conserva todas las tablas y archivos históricos.
begin;
create table public."MinutasIndependientes" (
  id uuid primary key,
  created_at timestamptz not null default now(),
  numero_contrato text not null check (numero_contrato ~ '^[0-9]+$'),
  anio_contrato integer not null check (anio_contrato between 2000 and 2099),
  actor text,
  version_plantilla text not null,
  plantilla_sha256 text not null,
  datos_minuta jsonb not null,
  storage_bucket text not null check (storage_bucket = 'minutas-independientes'),
  storage_path text not null unique,
  minuta_sha256 text not null
);
alter table public."MinutasIndependientes" enable row level security;
revoke all on public."MinutasIndependientes" from anon, authenticated;
grant select, insert, update on public."MinutasIndependientes" to service_role;
create index minutas_independientes_contrato_idx
  on public."MinutasIndependientes" (anio_contrato, numero_contrato);
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('minutas-independientes', 'minutas-independientes', false, 10485760,
  array['application/vnd.openxmlformats-officedocument.wordprocessingml.document']);
notify pgrst, 'reload schema';
commit;
