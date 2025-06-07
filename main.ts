import { Database } from "bun:sqlite";

class AlagometrosDB extends Database{
    constructor(path:string){
        super(path)
    }
}

const db = new AlagometrosDB("historico.db");

db.exec(await Bun.file("dbstart.sql").text())

Bun.serve({
  port:15694,
  error: error => {
    console.error(error);
    return new Response("Internal Server Error", { status: 500 });
  },
  routes: {
    "/":{
      GET: async req => {
        return new Response(Bun.file(`./www/index.htm`))
      }
    },
    "/assets/*":{
      GET: async req => {
        let file = await Bun.file(`./www/assets/${req.url.split("/")[4]}`)
        if (await file.exists()) {
          return new Response(await file.text(), {status:200,headers:{"Content-Type":file.type}})
        } else {
          return new Response(null,{status:404}) 
        }
      }
    },
    "/sensor/atualizar":{
      POST: async req => {
        let sensor = <Sensor>await req.json();
        let epoch = Date.now()/1000

        db.query(
          "INSERT INTO HistoricoSensores (epoch, sensorid, humidade, temperatura, alagado, zonas) VALUES (?, ?, ?, ?, ?, ?)"
        ).run(epoch, sensor.sensorid, sensor.humidade, sensor.temperatura, sensor.alagado, sensor.zonas.join(" "));
        return Response.json("OK", { status: 201 });
      },
    },
    "/sensor/listar": {
      GET: () => {
        let sensores = <DBSensor[]>db.query(
          "SELECT * FROM HistoricoSensores ORDER BY epoch DESC"
        ).all();
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
    // "/sensor/listar/historico": {
    //   GET: () => {
    //     return Response.json((<DBSensor[]>db.query(
    //       "SELECT * FROM HistoricoSensores ORDER BY epoch DESC"
    //     ).all()).map(DBSensorToEpochSensor));
    //   }
    // },
    "/sensor/:id": {
      GET: req => {
        let sensor = <DBSensor>db.query(
          "SELECT * FROM HistoricoSensores WHERE sensorid = ? ORDER BY epoch DESC LIMIT 1"
        ).get(parseInt(req.params.id));
        if (!sensor) {
          return new Response("Não Encontrado", { status: 404 });
        }
        return Response.json(DBSensorToEpochSensor(sensor));
      }
    },
    "/sensor/:id/historico": {
      GET: req => {
        return Response.json((<DBSensor[]>db.query(
          "SELECT * FROM HistoricoSensores WHERE sensorid = ? ORDER BY epoch"
        ).all(parseInt(req.params.id))).map(DBSensorToEpochSensor));
      }
    },
    "/zona/atualizar":{
      POST: async req => {
        const zona = <EpochZona>await req.json();
        const epoch = Date.now()/1000
        db.query(
          "INSERT INTO HistoricoZonas (epoch, zonaid, alagada) VALUES (?, ?, ?)"
        ).run(epoch, zona.zonaid, zona.alagada);
        return Response.json("OK", { status: 201 });
      },
    },
    "/zona/listar": {
      GET: () => {
        let zonas = <DBZona[]>db.query(
          "SELECT * FROM HistoricoZonas ORDER BY epoch DESC LIMIT 1"
        ).all();
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
    "/zona/:id": {
      GET: req => {
        const zona = db.query(
          "SELECT * FROM HistoricoZonas WHERE zonaid = ? ORDER BY epoch DESC LIMIT 1"
        ).get(req.params.id);
        if (!zona) {
          return new Response("Não Encontrada", { status: 404 });
        }
        return Response.json(zona);
      },
    },
    "/zona/:id/historico": {
      GET: req => {
        return Response.json((<DBZona[]>db.query(
          "SELECT * FROM HistoricoZonas WHERE zonaid = ? ORDER BY epoch"
        ).all(parseInt(req.params.id))).map(DBZonaToEpochZona));
      }
    },
    "/var/:var": {
      OPTIONS: req => {
        return new Response(null,{status:204,headers:{
          "Allow": "OPTIONS, GET, PUT, DELETE"
        }});
      },
      GET: req => {
        const globalvar = <GlobalVar>db.query("SELECT * FROM GlobalVars WHERE varname = ?").get(req.params.var);
        if (!globalvar) {
          return Response.json(null,{status:203})
        } else {
          return Response.json(JSON.parse(globalvar.varval),{status:203});
        }
      },
      PUT: async req => {
        const globalvar = <GlobalVar>db.query(
          "SELECT * FROM GlobalVars WHERE varname = ?"
        ).get(req.params.var);
        if (!globalvar) {
          db.query(
            "INSERT INTO GlobalVars (varname, varval) VALUES (?, ?)"
          ).run(req.params.var,JSON.stringify(await req.json()))
          return Response.json("",{status:201})
        } else {
          db.query(
            "UPDATE GlobalVars SET varval = ? WHERE varname = ?"
          ).run(JSON.stringify(await req.json()),req.params.var)
          return Response.json("",{status:200});
        }
      },
      DELETE: req => {
        db.query(
          "DELETE FROM GlobalVars WHERE varname = ?"
        ).run(req.params.var)
        return Response.json("",{status:203});
      }
    },
    "/vars":{
      GET: async req => {
        let rawvars = (<GlobalVar[]>db.query(
          "SELECT * FROM GlobalVars ORDER BY varname"
        ).all()).map(vars=> `"${vars.varname}": ${vars.varval}`)
        return Response.json(JSON.parse(`{"count":${rawvars.length},"list":{${rawvars.join(",")}}}`))
      }
    }
  }
});

function DBSensorToEpochSensor(dbsensor:DBSensor):EpochSensor{
  return {
    "epoch": dbsensor.epoch,
    "sensorid": dbsensor.sensorid,
    "humidade": dbsensor.humidade,
    "temperatura": dbsensor.temperatura,
    "alagado": dbsensor.alagado==1?true:false,
    "zonas": dbsensor.zonas.split(" ").map(n=>parseInt(n))
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
    humidade: number,
    temperatura: number,
    alagado: boolean,
    zonas: number[]
}

interface EpochSensor extends Sensor {
    epoch: number
}

interface DBSensor {
    epoch: number,
    sensorid: number,
    humidade: number,
    temperatura: number,
    alagado: number,
    zonas: string
}

interface Zona {
    zonaid: number,
    alagada: boolean
}

interface EpochZona extends Zona {
    epoch: number
}

interface DBZona {
  epoch: number,
  zonaid: number,
  alagada: number
}

interface GlobalVar {
  varname: string,
  varval: string
}