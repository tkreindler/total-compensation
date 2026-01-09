import RequestPayload from "./RequestPayload";
import React, { useState } from "react";
import ResponsePayload from "./ResponsePayload";
import Plot from "react-plotly.js";


interface PlotData
{
    // cached request to see if we should repeat the request
    "request": RequestPayload

    // response payload from the api
    "response": ResponsePayload
}

interface State
{
    "plotData": PlotData | undefined
}
interface Props
{
    "request": RequestPayload | undefined
}

const PlotlyPlot: React.FC<Props> = ({ request }) =>
{
    const doAsyncRequest = async (request: RequestPayload) =>
    {
        // hit the API to do the processing
        const response = await fetch("/api/v1.0/plot/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            mode: "cors",
            body: JSON.stringify(request)
        });

        const data: ResponsePayload = await response.json()

        console.log("finished async plot request")
        
        const pretty = JSON.stringify(data, null, 4)
        console.log(pretty)

        console.log()

        // set state to asynchronously reload with the graph
        setState(prevState => ({
            ...prevState,
            plotData: {
                ...prevState.plotData,
                request: request,
                response: data,
            }
        }));
    }

    // Create a state to store the input fields
    const [state, setState] = useState<State>({ "plotData": undefined });

    if (!request)
    {
        return (
            <div></div>
        )
    }

    const today = new Date();

    if (!state.plotData ||
        state.plotData.request !== request)
    {
        console.log("kicked off async plot request")

        const pretty = JSON.stringify(request, null, 4)
        console.log(pretty)

        doAsyncRequest(request)
            .catch(err => console.error(err))
        
        return(
            <div>Loading...</div>
        )
    }

    // has to be non null as in the check above
    const plotData: PlotData = state.plotData;

    const todayLine: Partial<Plotly.Shape> = {
        type: 'line',
        yref: 'paper', y0: 0, y1: 1,
        xref: 'x', x0: today, x1: today,
        line: {
            color: 'red',
            width: 2
        }
    }
    
    const layout: Partial<Plotly.Layout> = {
        title: {
            text: "Total Compensation"
        },
        xaxis: {
            title: {
                text: "Date"
            },
            type: 'date',
            range: [plotData.response[0].x[0], request.misc.endDate],
        },
        yaxis: {
            title: {
                text: "Money (USD)"
            },
            tickprefix: "$",
            tickformat: ",.2f",
            automargin: true,
        },
        shapes: [
            todayLine
        ]
    };

    const data: any[] = [...plotData.response]

    return (
        <div>
            <Plot style={{width: "90%", left: "auto", right: "auto"}}
                data={data}
                layout={layout}
            />
        </div>
    )
}

export default PlotlyPlot;