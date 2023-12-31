import RequestPayload, { AnnualBonus, AnnualBonuses, Misc, Pay, SigningBonus, Stock } from "./RequestPayload";
import React, { useState } from "react";
import FileSaver from 'file-saver';

interface State
{
    "payload": RequestPayload
}

interface Props
{
    initialState: RequestPayload;
    submitCallback: (payload: RequestPayload) => Promise<void>;
    saveCallback: (payload: RequestPayload) => Promise<void>;
}

const Form: React.FC<Props> = ({ initialState, submitCallback, saveCallback }) =>
{
    // Create a state to store the input fields
    const [state, setState] = useState<State>({ "payload": initialState });

    //#region miscellaneous

    // Create a function to handle changing the value of an input field
    const handleMiscellaneous = (event: React.ChangeEvent<HTMLInputElement>) =>
    {
        setState(prevState =>
        {
            const misc: Misc = {
                ...prevState.payload.misc,
            }

            switch (event.target.name)
            {
                case "predictedInflation":
                    misc.predictedInflation = +event.target.value;
                    break;

                case "startDate":
                    misc.startDate = event.target.value;
                    break;

                case "endDate":
                    misc.endDate = event.target.value;
                    break;

                default:
                    break;
            }

            return ({
                payload: {
                    ...prevState.payload,
                    misc: misc
                }
            })
        });
    };

    const miscellaneous = (
        <div>
            <h3>Miscellaneous</h3>
            <label>
                <span>Start Date </span>
                <input
                    type="date"
                    name="startDate"
                    value={state.payload.misc.startDate}
                    onChange={(event) => handleMiscellaneous(event)}
                />
            </label>
            <br />
            <label>
                <span>End Date </span>
                <input
                    type="date"
                    name="endDate"
                    value={state.payload.misc.endDate}
                    onChange={(event) => handleMiscellaneous(event)}
                />
            </label>
            <br />
            <label>
                <span>Predicted future inflation (for stock price prediction) </span>
                <input
                    type="number"
                    name="predictedInflation"
                    value={Number(state.payload.misc.predictedInflation).toString()}
                    onChange={(event) => handleMiscellaneous(event)}
                    min={1}
                    max={1.3}
                    step={0.01}
                />
            </label>
            <hr />
        </div>
    )

    //#endregion

    //#region signingBonus

    // Create a function to handle changing the value of an input field
    const handleSigningBonusChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    {
        setState(prevState =>
        {
            const signingBonus: SigningBonus = {
                ...prevState.payload.bonus.signing,
            }

            switch (event.target.name)
            {
                case "amount":
                    signingBonus.amount = +event.target.value;
                    break;

                case "durationYears":
                    signingBonus.duration.years = +event.target.value;
                    break;

                case "durationMonths":
                    signingBonus.duration.months = +event.target.value;
                    break;

                case "name":
                    signingBonus.name = event.target.value;
                    break;

                default:
                    break;
            }

            return ({
                payload: {
                    ...prevState.payload,
                    bonus: {
                        ...prevState.payload.bonus,
                        signing: signingBonus
                    }
                }
            })
        });
    };

    const signingBonus = (
        <div>
            <h3>Signing Bonus</h3>
            <label>
                <span>Name </span>
                <input
                    type="text"
                    name="name"
                    value={state.payload.bonus.signing.name}
                    onChange={(event) => handleSigningBonusChange(event)}
                />
            </label>
            <br />
            <label>
                <span>Total amount of the Signing Bonus (USD) </span>
                <input
                    type="number"
                    name="amount"
                    value={Number(state.payload.bonus.signing.amount).toString()}
                    onChange={(event) => handleSigningBonusChange(event)}
                    min={0}
                    step={0.01}
                />
            </label>
            <br />
            <br />
            <span>Total duration until signing bonus fully vests: </span>
            <br />
            <label>
                <span>Years: </span>
                <input
                    type="number"
                    name="durationYears"
                    value={Number(state.payload.bonus.signing.duration.years).toString()}
                    onChange={(event) => handleSigningBonusChange(event)}
                    min={0}
                    step={1}
                />
            </label>
            <br />
            <label>
                <span>Months: </span>
                <input
                    type="number"
                    name="durationMonths"
                    value={Number(state.payload.bonus.signing.duration.months).toString()}
                    onChange={(event) => handleSigningBonusChange(event)}
                    min={0}
                    step={1}
                />
            </label>
            <hr />
        </div>
    )

    //#endregion

    //#region annualBonus

    // Create a function to handle adding a new input field
    const addPastAnualBonus = () =>
    {
        const newBonus: AnnualBonus =
        {
            endDate: "2022-01-10",
            multiplier: 0.1,
        };

        setState(prevState => ({
            payload: {
                ...prevState.payload,
                bonus: {
                    ...prevState.payload.bonus,
                    annual: {
                        ...prevState.payload.bonus.annual,
                        past: [
                            ...prevState.payload.bonus.annual.past,
                            newBonus
                        ]
                    }
                }
            }
        }));
    };

    // Create a function to handle removing an existing input field
    const removePastAnnualBonus = (index: number) =>
    {
        setState(prevState =>
        {
            // make a copy excluding the provided index
            const newBonusAmounts = prevState.payload.bonus.annual.past
                .filter((_, i) => i !== index);


            return ({
                payload: {
                    ...prevState.payload,
                    bonus: {
                        ...prevState.payload.bonus,
                        annual: {
                            ...prevState.payload.bonus.annual,
                            past: newBonusAmounts
                        }
                    }
                }
            });
        });
    };

    // Create a function to handle changing the value of an input field
    const handlePastAnnualChange = (index: number, event: React.ChangeEvent<HTMLInputElement>) =>
    {
        const updateBonus = (prevBonus: AnnualBonus) =>
        {
            // shallow copy stock object
            const bonus: AnnualBonus = Object.assign({}, prevBonus)

            switch (event.target.name)
            {
                case "multiplier":
                    bonus.multiplier = +event.target.value;
                    break;

                case "endDate":
                    bonus.endDate = event.target.value;
                    break;

                default:
                    break;
            }

            return bonus;
        }

        setState(prevState =>
        {
            // make a copy excluding the provided index
            const newBonus = prevState.payload.bonus.annual.past
                .map((pay, i) =>
                {
                    if (index === i)
                    {
                        return updateBonus(pay);
                    }
                    else
                    {
                        return pay;
                    }
                });

            return ({
                payload: {
                    ...prevState.payload,
                    bonus: {
                        ...prevState.payload.bonus,
                        annual: {
                            ...prevState.payload.bonus.annual,
                            past: newBonus
                        }
                    }
                }
            });
        });
    };

    const createPastAnnualBonus = (bonus: AnnualBonus, index: number) =>
    {
        return (
            <div>
                <label>
                    <span>End Date </span>
                    <input
                        type="date"
                        name="endDate"
                        value={bonus.endDate}
                        onChange={(event) => handlePastAnnualChange(index, event)}
                    />
                </label>
                <br />
                <label>
                    <span>Percent multiplier of base pay </span>
                    <input
                        type="number"
                        name="multiplier"
                        value={Number(bonus.multiplier).toString()}
                        onChange={(event) => handlePastAnnualChange(index, event)}
                        min={0}
                        max={1}
                        step={0.01}
                    />
                </label>
                <br />
                <button type="button" onClick={() => removePastAnnualBonus(index)}>
                    Remove
                </button>
                <hr />
            </div>
        )
    }
    // Create a function to handle changing the value of an input field
    const handleAnnualBonusDefaultsChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    {
        setState(prevState =>
        {
            const bonusDefaults: AnnualBonuses = {
                ...prevState.payload.bonus.annual,
            }

            switch (event.target.name)
            {
                case "default":
                    bonusDefaults.default = +event.target.value;
                    break;

                case "name":
                    bonusDefaults.name = event.target.value;
                    break;

                default:
                    break;
            }

            return ({
                payload: {
                    ...prevState.payload,
                    bonus: {
                        ...prevState.payload.bonus,
                        annual: bonusDefaults
                    }
                }
            })
        });
    };

    const annualBonus = (
        <div>
            <h3>Annual Bonus</h3>
            <label>
                <span>Name </span>
                <input
                    type="text"
                    name="name"
                    value={state.payload.bonus.annual.name}
                    onChange={(event) => handleAnnualBonusDefaultsChange(event)}
                />
            </label>
            <br />
            <label>
                <span>Default percent multiplier of base pay (used as a prediction for future years) </span>
                <input
                    type="number"
                    name="default"
                    value={Number(state.payload.bonus.annual.default).toString()}
                    onChange={(event) => handleAnnualBonusDefaultsChange(event)}
                    min={0}
                    max={1}
                    step={0.01}
                />
            </label>
            <hr />
            {state.payload.bonus.annual.past.map((bonus, index) => (
                createPastAnnualBonus(bonus, index)
            ))}
            <button type="button" onClick={addPastAnualBonus}>
                Add
            </button>
            <hr />
        </div>
    )

    //#endregion

    //#region basePay

    // Create a function to handle adding a new input field
    const addPay = () =>
    {
        const newPay: Pay =
        {
            startDate: "2022-01-10",
            amount: 0,
        };

        setState(prevState => ({
            payload: {
                ...prevState.payload,
                base: {
                    ...prevState.payload.base,
                    pay: [
                        ...prevState.payload.base.pay,
                        newPay
                    ]
                }
            }
        }));
    };

    // Create a function to handle removing an existing input field
    const removePay = (index: number) =>
    {
        setState(prevState =>
        {
            // make a copy excluding the provided index
            const newPay = prevState.payload.base.pay
                .filter((_, i) => i !== index);


            return ({
                payload: {
                    ...prevState.payload,
                    base: {
                        ...prevState.payload.base,
                        pay: newPay
                    }
                }
            });
        });
    };

    // Create a function to handle changing the value of an input field
    const handlePayChange = (index: number, event: React.ChangeEvent<HTMLInputElement>) =>
    {
        const updatePay = (prevPay: Pay) =>
        {
            // shallow copy stock object
            const pay: Pay = Object.assign({}, prevPay)

            switch (event.target.name)
            {
                case "amount":
                    pay.amount = +event.target.value;
                    break;

                case "startDate":
                    pay.startDate = event.target.value;
                    break;

                default:
                    break;
            }

            return pay;
        }

        setState(prevState =>
        {
            // make a copy excluding the provided index
            const newPay = prevState.payload.base.pay
                .map((pay, i) =>
                {
                    if (index === i)
                    {
                        return updatePay(pay);
                    }
                    else
                    {
                        return pay;
                    }
                });

            return ({
                payload: {
                    ...prevState.payload,
                    base: {
                        ...prevState.payload.base,
                        pay: newPay
                    }
                }
            });
        });
    };

    const createPay = (pay: Pay, index: number) =>
    {
        return (
            <div>
                <label>
                    <span>Start Date </span>
                    <input
                        type="date"
                        name="startDate"
                        value={pay.startDate}
                        onChange={(event) => handlePayChange(index, event)}
                    />
                </label>
                <br />
                <label>
                    <span>Annual base pay (USD) </span>
                    <input
                        type="number"
                        name="amount"
                        value={Number(pay.amount).toString()}
                        onChange={(event) => handlePayChange(index, event)}
                        min={0}
                        step={0.01}
                    />
                </label>
                <br />
                <button type="button" onClick={() => removePay(index)}>
                    Remove
                </button>
                <hr />
            </div>
        )
    }
    // Create a function to handle changing the value of an input field
    const handleBaseNameChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    {
        setState(prevState => ({
            payload: {
                ...prevState.payload,
                base: {
                    ...prevState.payload.base,
                    name: event.target.value
                }
            }
        }));
    };

    const base = (
        <div>
            <h3>Base Pay</h3>
            <label>
                <span>Name </span>
                <input
                    type="text"
                    value={state.payload.base.name}
                    onChange={(event) => handleBaseNameChange(event)}
                />
            </label>
            <hr />
            {state.payload.base.pay.map((pay, index) => (
                createPay(pay, index)
            ))}
            <button type="button" onClick={addPay}>
                Add
            </button>
            <hr />
        </div>
    )

    //#endregion

    //#region stocks

    // Create a function to handle adding a new input field
    const addStock = () =>
    {
        const newStock: Stock =
        {
            name: "",
            shares: 0,
            startDate: "2022-01-10",
            endDate: "2022-01-10",
        };

        setState(prevState => ({
            payload: {
                ...prevState.payload,
                stocks: [
                    ...prevState.payload.stocks,
                    newStock
                ]
            }
        }));
    };

    // Create a function to handle removing an existing input field
    const removeStock = (index: number) =>
    {
        setState(prevState =>
        {
            // make a copy excluding the provided index
            const newStocks = prevState.payload.stocks
                .filter((_, i) => i !== index);

            return ({
                payload: {
                    ...prevState.payload,
                    stocks: newStocks
                }
            });
        });
    };

    // Create a function to handle changing the value of an input field
    const handleStockChange = (index: number, event: React.ChangeEvent<HTMLInputElement>) =>
    {
        const updateStock = (prevStock: Stock) =>
        {
            // shallow copy stock object
            const stock: Stock = Object.assign({}, prevStock)

            switch (event.target.name)
            {
                case "name":
                    stock.name = event.target.value;
                    break;

                case "shares":
                    stock.shares = +event.target.value;
                    break;

                case "startDate":
                    stock.startDate = event.target.value;
                    break;

                case "endDate":
                    stock.endDate = event.target.value;
                    break;

                default:
                    break;
            }

            return stock;
        }

        setState(prevState =>
        {
            // make a copy excluding the provided index
            const newStocks = prevState.payload.stocks
                .map((stock, i) =>
                {
                    if (index === i)
                    {
                        return updateStock(stock);
                    }
                    else
                    {
                        return stock;
                    }
                });

            return ({
                payload: {
                    ...prevState.payload,
                    stocks: newStocks
                }
            });
        });
    };

    const createStock = (stock: Stock, index: number) =>
    {
        return (
            <div>
                <label>
                    <span>Name </span>
                    <input
                        type="text"
                        name="name"
                        value={stock.name}
                        onChange={(event) => handleStockChange(index, event)}
                    />
                </label>
                <br />
                <label>
                    <span>Number of Shares </span>
                    <input
                        type="number"
                        name="shares"
                        value={Number(stock.shares).toString()}
                        onChange={(event) => handleStockChange(index, event)}
                        min={0}
                        step={1}
                    />
                </label>
                <br />
                <label>
                    <span>Start Date </span>
                    <input
                        type="date"
                        name="startDate"
                        value={stock.startDate}
                        onChange={(event) => handleStockChange(index, event)}
                    />
                </label>
                <br />
                <label>
                    <span>End Date </span>
                    <input
                        type="date"
                        name="endDate"
                        value={stock.endDate}
                        onChange={(event) => handleStockChange(index, event)}
                    />
                </label>
                <br />
                <button type="button" onClick={() => removeStock(index)}>
                    Remove
                </button>
                <hr />
            </div>
        )
    }

    const stocks = (
        <div>
            <h3>Stocks</h3>
            <hr />
            {state.payload.stocks.map((stock, index) => (
                createStock(stock, index)
            ))}
            <button type="button" onClick={addStock}>
                Add
            </button>
            <hr />
        </div>
    )

    //#endregion

    const downloadPayload = (payload: RequestPayload) =>
    {
        const pretty = JSON.stringify(payload, null, 4);

        const blob = new Blob([pretty], { type: "application/json" })

        FileSaver.saveAs(blob, "total-compensation.json")
    }

    const importPayload: React.ChangeEventHandler<HTMLInputElement> = (e: React.ChangeEvent<HTMLInputElement>) =>
    {
        const files = e.target.files;

        if (!files)
        {
            console.error("no files found in upload");
            return;
        }

        const file = files[0];

        if (file.type !== "application/json")
        {
            console.error("Uploaded file is not a json file");
            return;
        }

        const reader = new FileReader();
        reader.onload = () =>
        {
            // define the onload callback
            const result = JSON.parse(reader.result as string) as RequestPayload;

            setState(prevState => ({
                ...prevState,
                payload: result
            }));
        };

        reader.readAsText(file);
    }

    // Use the map function to render the input fields from the state
    return (
        <form>
            {base}
            {signingBonus}
            {annualBonus}
            {stocks}
            {miscellaneous}
            <button type="button" onClick={async () => await submitCallback(state.payload)}>
                Submit
            </button>
            <button type="button" onClick={async () => await saveCallback(state.payload)}>
                Save
            </button>
            <span> </span>
            <button type="button" onClick={async () => await downloadPayload(state.payload)}>
                Export
            </button>
            <button type="button" onClick={() => document.getElementById('import-button-hidden')!.click()}>
                Import
            </button>
            <input
                id="import-button-hidden"
                type="file"
                onChange={importPayload}
                style={{ display: "none" }}
            />
        </form>
    );
}

export default Form;