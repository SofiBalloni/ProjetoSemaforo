CREATE TABLE IF NOT EXISTS HistoricoSensores (
    epoch BIGINT,
    sensorid INTEGER,
    humidade INTEGER,
    temperatura INTEGER,
    alagado BOOLEAN,
    zonas TEXT,
    PRIMARY KEY (sensorid, epoch)
);

CREATE TABLE IF NOT EXISTS HistoricoZonas (
    epoch BIGINT,
    zonaid INTEGER,
    alagada BOOLEAN,
    PRIMARY KEY (zonaid, epoch)
);

CREATE TABLE IF NOT EXISTS GlobalVars (
    varname TEXT,
    varval TEXT,
    PRIMARY KEY (varname)
);