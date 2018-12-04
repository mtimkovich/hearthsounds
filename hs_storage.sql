-- create hs_storage.csv with:
-- gsutil ls gs://hearthsounds | sed 's#.*/##' > hs_storage.csv
drop table if exists sounds;
create virtual table sounds using fts4(file_name text);
.import hs_storage.csv sounds
