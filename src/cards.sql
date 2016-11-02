drop table if exists cards;

create table cards (
    id integer primary key,
    card_id text unique,
    name text,
    image text,
    sounds text,
    created datetime current_timestamp
);
