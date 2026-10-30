# Native kernel bounded screen：U04 prefetch／U14 IQ2_S nt1

TASK_ID LUNA-20261012-027 continuation，2026-10-30。使用者授權未測候選。只編譯CPU小工具、連結當輪current-best CPU/ggml libraries；無R4、CUDA build、引擎source整合或部署。parent負責fresh process/current-best/lib/config/source/pack gate與啟動，作者未SSH、run或量測。

CLI：`nativebench.exe <lp> <base|prefetch4096|iq2s_nt1> <experts.bin> <native_experts.txt>`。每個mode是新程序，BelowNormal、hard pin後才第一次進Strata的feature/variant/quant路徑。原MT1必須1、MT_MIN必須absent；base/iq2s_nt1保留原env，prefetch4096只在firstcall前設STRATA_IQ_PREFETCH=4096。沒有失敗fallback；iq2s_nt1要求CPU有VNNI，否則FAIL。

資料：實際metadata五種GU各選六層、每層三個expert（18/type，完整模式90），公式與上輪相同（layer選取均勻、expert=(11+37*j+5*layer)%512），blob依實際offset/size從native experts.bin讀取。iq2s_nt1只load type22，18samples。每sample輸出原始bytes SHA256與精確layer/expert/offset/size，固定seed12345合成3×H輸入並hash；不輸出任何模型文字。

完整native working set每型assert>20MiB；部分GU-only資料少於20MiB（如18個IQ2_XXS約15.2MB），所以GU-only不能宣稱全是超L3 stream。sample數固定、不增大、不新增flush buffer；combined含實際down資料，較適合判斷本screen。與生產多worker/row partition仍有差別，不能直接外推整機。

U04：parent每P/E core作base/prefetch4096/base短交錯新程序。每程序五格式×nt1/2/3×GU-only/combined，每格一個完整warm pass＋五個timed passes；無額外reps。env在firstcall前固定，不能在同程序切換static-prefetch cache。真正bitwise關卡：parent核對三程序的ITEM/input/activation SHA與每type/nt的h/out HASH完全相同；任一不同即FAIL，不拿同函式自比當跨env證明。NUMERIC同程序只檢查native路徑的自我重現、finite；明確不聲稱已證4096對2048。

U14：mode iq2s_nt1同程序A=native_gu_rows，B僅type22/nt1直接iq256_gu_rows_v(kIq256Vnni,...)（明確VNNI-only，不用P-core auto gather）。nt2/3 B與A皆用原native_gu_rows，確認未變。先同input A/B數值：h/down finite、maxabs與different-bit counts、SHA；h差異<=1e-4×max(1,max|ref h|)只作機械初篩，不代表品質。nt2/3保持路徑要求bitwise相等。每格一warm＋五AB/BA交錯timed passes，不加輪。

combined精確沿用實際pool dispatch：down42用act_quant_any與q2_rows_any；down20用native_quant_h與native_down_rows。所有buffer預配置，計時內無配置/hash/byte比較/檔案I/O，RAW和SUM單位us/expert。數值比較、hash、樣本讀取均在計時外。control的library SHA由parent當輪核對保存，不以本機source當遠端權威。

停止：open/geometry/MT1/MT_MIN/pin/VNNI/finite/h-screen/unchanged-bitwise任何失敗立即exit3；不改mode或數據重試替代路徑。prefetch跨程序parity未過不得作速度結論。五次median僅短screen，parent需看C/C2漂移與raw；不能以一格正值稱整機+10%。IQ2_S nt1若有小收益仍須真實權重/品質與整機gate，這輪不部署。

產物：ENV、ITEM(sample SHA)、COVER、INPUT_SHA256、WORKING_SET、ACT_SHA256、NUMERIC、HASH、RAW、SUM、DONE。parent保存exe/lib/source/build/metadata hashes與log，不發私人權重/輸入到GitHub。無language-quality測試、無所有24576expert掃描、無實際h分布；只有90或18個合成輸入screen。

本地驗證：僅靜態核對，未本機編譯（遠端Strata headers/libs才是實際來源）；由parent於fresh gate後build，build失敗保留log並修同流程，不下載其他版本或換library。
