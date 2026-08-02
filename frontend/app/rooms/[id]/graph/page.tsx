"use client";

import { useParams } from "next/navigation";

import CognitiveGraph from "@/components/ai/CognitiveGraph";


export default function GraphPage() {

  const params = useParams();

  const roomId = Number(
    params.id
  );

  return (

    <div className="p-6">

      <h1 className="text-2xl font-bold mb-4">

        Rework Cognitive Graph

      </h1>

      <CognitiveGraph roomId={roomId} />

    </div>
  );
}