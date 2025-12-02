import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export default function CandidateProfile({ id }:any) {
    const [data, setData] = useState(null);

    useEffect(() => {
        api.get(`/candidate/${id}`).then((res) => setData(res.data));
    }, [id]);

    if (!data) return <p>Loading...</p>;

    return (
        <Card className="mt-10">
            <CardHeader>
                <CardTitle>{data.name}</CardTitle>
            </CardHeader>
            <CardContent>
                <p><strong>Email:</strong> {data.email}</p>
                <p><strong>Phone:</strong> {data.phone}</p>
                <p><strong>Experience:</strong> {data.experience_years} years</p>
                <p><strong>Skills:</strong> {data.skills}</p>
                <p><strong>Education:</strong> {data.education}</p>
                <p className="mt-4"><strong>Summary:</strong> {data.summary}</p>
            </CardContent>
        </Card>
    );
}
