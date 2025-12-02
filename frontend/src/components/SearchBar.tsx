import { useState } from "react";
import { api } from "../lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";

export default function SearchBar() {
    const [query, setQuery] = useState("");
    const [result, setResult] = useState("");

    const handleSearch = async () => {
        const res = await api.post("/search", { query });
        setResult(res.data.result);
    };

    return (
        <Card className="w-full max-w-xl mx-auto mt-10">
            <CardHeader><CardTitle>Search Candidates</CardTitle></CardHeader>
            <CardContent>
                <Input
                    value={query}
                    placeholder="e.g. 5 years Java + AWS"
                    onChange={(e) => setQuery(e.target.value)}
                    className="mb-4"
                />
                <Button onClick={handleSearch}>Search</Button>
                {result && (
                    <pre className="mt-4 p-4 bg-gray-100 rounded">{result}</pre>
                )}
            </CardContent>
        </Card>
    );
}
