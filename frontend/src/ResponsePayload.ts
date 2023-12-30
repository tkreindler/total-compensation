type ResponsePayload = Series[]

export default ResponsePayload

export interface Series {
    name: string;
    x: string[];
    y: number[];
}
