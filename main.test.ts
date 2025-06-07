import { describe, expect, it } from "bun:test";
import { randomInt } from "crypto";

const apiURL = "http://localhost:15694"

describe("Sensores", () => {
    let sensores = []
    for (let i = 0; i < 500; i++) {
        sensores.push(gerarSensor(i))
    }
    it("Deve criar 500 sensores", async () => {
        sensores.forEach(async sensor=> {
            const response = await fetch(`${apiURL}/sensor/atualizar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(sensor),
            });
            expect(response.status).toBe(201);
        });
        await new Promise(resolve => setTimeout(resolve, 100));
    });

    it("Deve retornar os 500 sensores individualmente", async () => {
        sensores.forEach(async sensor =>{
            const response = await fetch(`${apiURL}/sensor/${sensor.zonaid}`);
            expect(response.status).toBe(200);
            const res_sensor = <EpochSensor>await response.json();
            
            expect(res_sensor.epoch).toBeLessThan(Date.now()/1000);
            expect(res_sensor.zonaid).toBe(sensor.zonaid);
            expect(res_sensor.humidade).toBe(sensor.humidade)
            expect(res_sensor.temperatura).toBe(sensor.temperatura);
            expect(res_sensor.alagada).toBe(sensor.alagada);
            expect(res_sensor.zonas).toEqual(sensor.zonas);
        });
        await new Promise(resolve => setTimeout(resolve, 100));
    });

    it("Deve Atualizar os 500 sensores", async () => {
        sensores.forEach(async sensor=> {
            const response = await fetch(`${apiURL}/sensor/atualizar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(gerarSensor(sensor.zonaid)),
            });
            expect(response.status).toBe(201);
        });
        await new Promise(resolve => setTimeout(resolve, 100));
    });
})

describe("Zonas", () => {
    let zonas = []
    for (let i = 0; i < 100; i++) {
        zonas.push(gerarZona(i))
    }

    it("Deve criar 100 zonas", async () => {
        zonas.forEach(async zona=> {
            const response = await fetch(`${apiURL}/zona/atualizar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(zona),
            });
            expect(response.status).toBe(201);
        });
        await new Promise(resolve => setTimeout(resolve, 100));
    });

    it("Deve retornar as 100 zonas individualmente", async () => {
        zonas.forEach(async zona =>{
            const response = await fetch(`${apiURL}/zona/${zona.zonaid}`);
            expect(response.status).toBe(200);
            const res_sensor = <EpochSensor>await response.json();
            
            expect(res_sensor.epoch).toBeLessThan(Date.now()/1000);
            expect(res_sensor.zonaid).toBe(zona.zonaid);
            expect(res_sensor.alagada).toBe(zona.alagada);
        });
        await new Promise(resolve => setTimeout(resolve, 100));
    });

    it("Deve Atualizar as 100 zonas", async () => {
        zonas.forEach(async zona=> {
            const response = await fetch(`${apiURL}/zona/atualizar`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(gerarZona(zona.zonaid)),
            });
            expect(response.status).toBe(201);
        });
        await new Promise(resolve => setTimeout(resolve, 100));
    });
})

interface Sensor {
    zonaid: number,
    humidade: number,
    temperatura: number,
    alagada: boolean,
    zonas: number[]
}

interface EpochSensor extends Sensor {
    epoch: number
}

interface Zona {
    zonaid: number,
    alagada: boolean
}

interface EpochZona extends Zona {
    epoch: number
}


function gerarSensor(sensorid:number): Sensor {
    return {
        zonaid: sensorid,
        humidade: randomInt(0, 100),
        temperatura: randomInt(-50, 50),
        alagada: Math.random() > 0.5,
        zonas: Array.from({ length: randomInt(1, 5) }, () => randomInt(1, 100))
    };
}

function gerarZona(zonaid:number): Zona {
    return {
        zonaid: zonaid,
        alagada: Math.random() > 0.5
    };
}