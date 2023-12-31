import { useState } from "react";
import Form from "./Form";
import RequestPayload, { defaultRequestPayload } from "./RequestPayload";
import { useCookies } from "react-cookie";

interface State
{
  "request": RequestPayload | undefined,
  "plotModule": typeof import("./Plot") | undefined
}

function App()
{
  // Create a state to store the input fields
  const [state, setState] = useState<State>({ "request": undefined, "plotModule": undefined });

  const [cookies, setCookie] = useCookies(['payload']);

  let requestPayload;
  if (cookies.payload)
  {
    requestPayload = cookies.payload;
  }
  else
  {
    requestPayload = defaultRequestPayload;
    setCookie("payload", defaultRequestPayload);
  }

  const importPlotlyPlot = async () =>
  {
    const plotModule = await import("./Plot")

    setState(prevState => ({
      ...prevState,
      plotModule: plotModule
    }));
  }

  let plotJsx;

  // Dynamically load plotly if not already loaded
  if (!state.plotModule)
  {
    importPlotlyPlot()
      .catch(err => console.error(err))

    plotJsx = (
      <div></div>
    )
  }
  else
  {
    const PlotlyPlot = state.plotModule.default;

    plotJsx = (
      <PlotlyPlot request={state.request} />
    )
  }

  // Use the map function to render the input fields from the state
  return (
    <div className="App">
      <h1>Total Compensation Graph</h1>
      <p>Source: <a href="https://github.com/tkreindler/total-compensation">https://github.com/tkreindler/total-compensation</a></p>
      <Form
        initialState={requestPayload}
        submitCallback={async (request: RequestPayload) =>
        {
          setState(prevState => ({
            ...prevState,
            "request": {
              ...request
            }
          }));
        }}
        saveCallback={async payload => setCookie("payload", payload)}
      ></Form>
      <br />
      {plotJsx}
    </div>
  );
}

export default App;
