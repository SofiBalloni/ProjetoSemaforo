CREATE TABLE IF NOT EXISTS HistoricoSensores (
    epoch BIGINT,
    sensorid INTEGER,
    zonas TEXT,
    alagado BOOLEAN,
    PRIMARY KEY (sensorid, epoch),
);

CREATE TABLE IF NOT EXISTS HistoricoZonas (
    epoch BIGINT,
    zonaid INTEGER,
    alagada BOOLEAN,
    PRIMARY KEY (zonaid, epoch),
);