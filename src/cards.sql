drop table if exists cards;

create table cards (
    id int not null auto_increment,
    card_id varchar(50) not null,
    name varchar(40),
    image varchar(255),
    sounds text,
    primary key (id),
    unique key (card_id)
);
