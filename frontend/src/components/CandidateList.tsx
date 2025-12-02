import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";

export default function CandidateList({ onSelect }: any) {
    const [candidates, setCandidates] = useState([]);

    useEffect(() => {
        api.get("/candidates").then((res) => setCandidates(res.data));
    }, []);

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-10">
            {candidates.map((c) => (
                <Card key={c.id}>
                    <CardHeader>
                        <CardTitle>{c.name || "Unnamed Candidate"}</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p>Email: {c.email}</p>
                        <p>Experience: {c.experience_years} years</p>
                        <Button className="mt-2" onClick={() => onSelect(c.id)}>
                            View Details
                        </Button>
                    </CardContent>
                </Card>
            ))}
        </div>
    );
}
