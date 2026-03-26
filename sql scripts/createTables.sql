DROP TABLE routes

DROP TABLE airports

DROP TABLE airlines


CREATE TABLE airports
(
AirportID INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
Code varchar(3) NOT NULL UNIQUE,
City varchar(64) NOT NULL,
Country varchar(64) NOT NULL,
DateAdded timestamp NOT NULL DEFAULT NOW(),
DateModified timestamp NOT NULL DEFAULT NOW()
)




CREATE TABLE airlines
(
AirlineID INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
Code varchar(2) NOT NULL UNIQUE,
Name varchar(64) NOT NULL,
DateAdded timestamp NOT NULL DEFAULT NOW(),
DateModified timestamp NOT NULL DEFAULT NOW()
)




CREATE TABLE routes
(
ID INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
AirlineID INT references airlines(AirlineID),
OriginAirportID INT references airports(AirportID),
DestinationAirportID INT references airports(AirportID),
DateAdded timestamp NOT NULL DEFAULT NOW(),
DateModified timestamp NOT NULL DEFAULT NOW()
)