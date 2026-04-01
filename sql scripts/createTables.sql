DROP TABLE routes

DROP TABLE airports

DROP TABLE airlines


CREATE TABLE airports
(
Code varchar(3) NOT NULL UNIQUE PRIMARY KEY,
City varchar(64) NOT NULL,
Country varchar(64) NOT NULL,
DateAdded timestamp NOT NULL DEFAULT NOW(),
DateModified timestamp NOT NULL DEFAULT NOW()
)




CREATE TABLE airlines
(
Code varchar(2) NOT NULL UNIQUE PRIMARY KEY,
Name varchar(64) NOT NULL,
DateAdded timestamp NOT NULL DEFAULT NOW(),
DateModified timestamp NOT NULL DEFAULT NOW()
)




CREATE TABLE routes
(
RouteID INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
Airline varchar(2) NOT NULL REFERENCES airlines(Code),
OriginAirport varchar(3) NOT NULL REFERENCES airports(Code),
DestinationAirport varchar(3) NOT NULL REFERENCES airports(Code),
DateAdded timestamp NOT NULL DEFAULT NOW(),
DateModified timestamp NOT NULL DEFAULT NOW(),
CONSTRAINT unique_route UNIQUE (Airline, OriginAirport, DestinationAirport)
)

INSERT INTO airlines(code, name)
VALUES ('FR', 'Ryanair')




CREATE TABLE schedules (
    ScheduleID    INTEGER   PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    RouteID       INTEGER   NOT NULL REFERENCES routes(RouteID),
    FlightDate    DATE      NOT NULL,
    DateAdded timestamp NOT NULL DEFAULT NOW(),
    DateModified timestamp NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_schedule UNIQUE (RouteID, FlightDate)
);