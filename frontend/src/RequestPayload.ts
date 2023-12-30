interface RequestPayload {
    base: Base;
    bonus: Bonus;
    stocks: Stock[];
    misc: Misc;
}

export default RequestPayload

export interface Base {
    name: string;
    pay: Pay[];
}

export interface Bonus {
    annual: AnnualBonuses;
    signing: SigningBonus;
}

export interface Stock {
    name: string;
    shares: number;
    startDate: string;
    endDate: string;
}

export interface AnnualBonuses {
    name: string;
    default: number;
    past: AnnualBonus[];
}

export interface AnnualBonus {
    endDate: string;
    multiplier: number;
}

export interface SigningBonus {
    name: string;
    amount: number;
    duration: {
        years: number;
        months: number;
    };
}

export interface Pay {
    startDate: string;
    amount: number;
}

export interface Misc {
    startDate: string;
    endDate: string;
    predictedInflation: number;
}

export const defaultRequestPayload: RequestPayload = {
    "base": {
        "name": "Base Pay",
        "pay": [
            {
                "startDate": "2022-01-10",
                "amount": 100000
            },
        ]
    },
    "bonus": {
        "annual": {
            "name": "Annual Bonus",
            "default": 0.10,
            "past": []
        },
        "signing": {
            "name": "Signing Bonus",
            "amount": 10000,
            "duration": {
                "years": 1,
                "months": 0,
            }
        }
    },
    "stocks": [
        {
            "name": "On Hire Stock Award",
            "shares": 100,
            "startDate": "2022-01-10",
            "endDate": "2025-08-15"
        }
    ],
    "misc": {
        "startDate": "2022-01-10",
        "endDate": "2026-01-10",
        "predictedInflation": 1.03
    }
}
