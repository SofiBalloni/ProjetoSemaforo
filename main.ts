import { Database } from "bun:sqlite";

class AlagometrosDB extends Database{
    constructor(path:string){
        super(path)
    }
}

const db = new AlagometrosDB("historico.db");

db.exec(await Bun.file("dbstart.sql").text())

Bun.serve({port:4000,routes: {
    "/sensor/atualizar":{
      POST: async req => {
        let sensor = <Sensor>await req.json();
        let epoch = Date.now()*1000

        db.query(`INSERT INTO HistoricoSensores (epoch, sensorid, zonas, alagado) VALUES (?, ?, ?, ?)`,).run(epoch, sensor.sensorid, sensor.zonas.join(" "), sensor.alagado);
        return Response.json("OK", { status: 201 });
      },
    },

    "/sensor/listar": {
      GET: () => {
        let sensores = <DBSensor[]>db.query("SELECT * FROM HistoricoSensores ORDER BY epoch DESC").all();
        let sensoresIdentificados = new Set<number>();
        let sensoresFiltrados = sensores.filter((sensor)=>{
          if (sensoresIdentificados.has(sensor.sensorid)){
            return false
          } else {
            sensoresIdentificados.add(sensor.sensorid)
            return true
          }
        })        
        return Response.json(sensoresFiltrados.map(DBSensorToEpochSensor));
      }
    },
    "/sensor/:id": {
      GET: req => {
        let sensor = <DBSensor>db.query("SELECT * FROM HistoricoSensores WHERE sensorid = ? ORDER BY epoch DESC LIMIT 1").get(parseInt(req.params.id));
        if (!sensor) {
          return new Response("Não Encontrado", { status: 404 });
        }
        return Response.json(DBSensorToEpochSensor(sensor));
      }
    },
    "/zona/listar": {
      GET: () => {
        let zonas = <DBZona[]>db.query("SELECT * FROM HistoricoZonas ORDER BY epoch DESC LIMIT 1").all();
        let zonaIdentificada = new Set<number>();
        return Response.json(zonas.filter((zona)=>{
          if (zonaIdentificada.has(zona.zonaid)){
            return false
          } else {
            zonaIdentificada.add(zona.zonaid)
            return true
          }
        }).map(DBZonaToEpochZona));
      }
    },
    "/zona/atualizar":{
      POST: async req => {
        const zona = <EpochZona>await req.json();
        const epoch = Date.now()*1000

        db.query(`INSERT INTO HistoricoZonas (epoch, zonaid, alagada) VALUES (?, ?, ?)`,).run(epoch, zona.zonaid, zona.alagada);
        return Response.json("OK", { status: 201 });
      },
    },
    "/zona/:id": {
      GET: req => {
        const zona = db.query("SELECT * FROM HistoricoZonas WHERE zonaid = ? ORDER BY epoch DESC LIMIT 1").get(req.params.id);
        if (!zona) {
          return new Response("Não Encontrada", { status: 404 });
        }
        return Response.json(zona);
      },
    },
    "/var/:var": {
      GET: req => {
        const globalvar = <GlobalVar>db.query("SELECT * FROM GlobalVars WHERE varname = ? ORDER BY epoch DESC LIMIT 1").get(req.params.var);
        if (!globalvar) {
          return Response.json(null,{status:203})
        } else {
          return Response.json(JSON.parse(globalvar.varval),{status:203});
        }
      },
      PUT: async req => {
        const globalvar = <GlobalVar>db.query("SELECT * FROM GlobalVars WHERE varname = ? ORDER BY epoch DESC LIMIT 1").get(req.params.var);
        if (!globalvar) {
          db.query("INSERT INTO GlobalVars (varname, varval) VALUES (?, ?)").run(req.params.var,JSON.stringify(await req.json()))
          return Response.json({status:201})
        } else {
          db.query("UPDATE GlobalVars SET varval = ? WHERE varname = ?").run(req.params.var,JSON.stringify(await req.json()))
          return Response.json({status:200});
        }
      },
      DELETE: req => {
        db.query("DELETE GlobalVars WHERE uma vez FLAMENGO sempre FLAMENGO")
        return Response.json({status:203});
      }
    }
  },
  error(error) {
    console.error(error);
    return new Response("Internal Server Error", { status: 500 });
  }
});

function DBSensorToEpochSensor(dbsensor:DBSensor):EpochSensor{
  return {
    "sensorid":dbsensor.sensorid,
    "zonas": dbsensor.zonas.split(" ").map(n=>parseInt(n)),
    "alagado": dbsensor.alagado==1?true:false,
    "epoch": dbsensor.epoch
  }
}

function DBZonaToEpochZona(dbzona:DBZona):EpochZona{
  return {
    "zonaid": dbzona.zonaid,
    "alagada": dbzona.alagada==1?true:false,
    "epoch": dbzona.epoch
  }
}

interface Sensor {
    sensorid: number,
    zonas: number[],
    alagado: boolean,
}

interface EpochSensor extends Sensor{
    epoch: number
}

interface DBSensor {
    sensorid: number,
    zonas: string,
    alagado: number,
    epoch: number
}

interface Zona {
    zonaid: number,
    alagada: boolean,
}

interface EpochZona extends Zona{
    epoch: number
}

interface DBZona {
  zonaid: number,
  alagada: number,
  epoch: number
}

interface GlobalVar {
  varname: string,
  varval: string
}