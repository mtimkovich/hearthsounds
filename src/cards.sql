drop table if exists cards;

create table cards (
    id integer primary key,
    card_id text unique,
    name text,
    image text,
    sounds text,
    created datetime current_timestamp
);

drop table if exists searches;

create table searches (
    id integer primary key,
    query text,
    card_id text,
    foreign key(card_id) references cards(card_id)
);
