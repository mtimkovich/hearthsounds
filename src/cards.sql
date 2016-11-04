drop table if exists cards;

create table cards (
    id integer primary key,
    card_id text unique,
    name text,
    image text,
    created datetime default current_timestamp
);

drop table if exists sounds;

create table sounds (
    id integer primary key,
    card_id text,
    name text,
    src text,
    foreign key(card_id) references cards(card_id)
);

drop table if exists searches;

create table searches (
    id integer primary key,
    query text,
    card_id text,
    created datetime default current_timestamp,
    foreign key(card_id) references cards(card_id),
    unique (query, card_id)
);

drop index if exists query_idx;
create index query_idx on searches(query);
