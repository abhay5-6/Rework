import {
  BrainCircuit
} from "lucide-react";


export default function LoadingSpinner({

  text = "Loading cognition..."

}: {

  text?: string
}) {

  return (

    <div className="
      flex
      flex-col
      items-center
      justify-center
      gap-5
      py-16
    ">

      {/* OUTER GLOW */}

      <div className="
        relative
        flex
        items-center
        justify-center
      ">

        {/* PULSE */}

        <div className="
          absolute
          h-20
          w-20
          rounded-full
          bg-primary/5
          animate-ping
        " />

        {/* CORE */}

        <div className="
          relative
          h-16
          w-16
          rounded-3xl
          border
          border-border
          bg-background
          flex
          items-center
          justify-center
          shadow-2xl
        ">

          <div className="
            absolute
            inset-0
            rounded-3xl
            border
            border-white/10
            animate-spin
          " />

          <BrainCircuit
            size={28}
            className="
              text-foreground
            "
          />

        </div>

      </div>


      {/* TEXT */}

      <div className="
        flex
        flex-col
        items-center
        gap-1
      ">

        <div className="
          text-sm
          font-medium
          text-neutral-200
        ">

          {text}

        </div>

        <div className="
          text-xs
          text-neutral-500
          tracking-wide
        ">

          Rework AI Workspace

        </div>

      </div>

    </div>
  );
}