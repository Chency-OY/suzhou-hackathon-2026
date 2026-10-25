import pytest
from app.rag import Fact, HashEmbedding, KnowledgeBase, SimpleStore
from app.rag.kb import chunk_label

FACTS = [
    Fact(id="f_dreams3", category="competitor", verified=False,
         statement="DREAMS-3 研究中玛仕度肽与司美格鲁肽头对头比较，复合达标比例更高"),
    Fact(id="f_dreams1", category="efficacy", verified=True,
         statement="DREAMS-1 研究显示 24 周 HbA1c 较基线下降，安慰剂组下降幅度较小"),
    Fact(id="f_gi", category="safety", verified=True,
         statement="常见不良反应为恶心、呕吐、腹泻等胃肠道反应，多在剂量递增阶段出现"),
    Fact(id="f_company", category="company", verified=False, statement="公司商业化产品覆盖肿瘤与慢病领域"),
    Fact(id="f_ind", category="indication", verified=True, caution="需以说明书为准",
         statement="已获批适应症包括体重管理与 2 型糖尿病，其他适应症尚在研究中"),
]


@pytest.fixture()
def kb():
    k = KnowledgeBase(embedder=HashEmbedding(), store=SimpleStore())
    k.index_facts(FACTS)
    return k


def test_top1_for_head_to_head(kb):
    assert kb.retrieve("司美格鲁肽 头对头", k=3)[0].id == "f_dreams3"


def test_only_verified_and_category_filters(kb):
    assert all(c.verified for c in kb.retrieve("研究", k=10, only_verified=True))
    got = kb.retrieve("不良反应", k=10, category="safety")
    assert [c.id for c in got] == ["f_gi"]
    both = kb.retrieve("适应症", k=10, only_verified=True, category="indication")
    assert [c.id for c in both] == ["f_ind"]


def test_caution_is_part_of_text(kb):
    assert "需以说明书为准" in kb.retrieve("适应症", k=1)[0].text


def test_reseed_is_idempotent(kb):
    n = kb.count()
    kb.index_facts(FACTS)
    assert kb.count() == n
    kb.reset()
    assert kb.count() == 0


def test_simple_store_persistence(tmp_path):
    path = tmp_path / "s.json"
    k1 = KnowledgeBase(embedder=HashEmbedding(), store=SimpleStore(path))
    k1.index_facts(FACTS)
    k2 = KnowledgeBase(embedder=HashEmbedding(), store=SimpleStore(path))
    assert k2.count() == len(FACTS)
    assert k2.retrieve("胃肠道 恶心", k=1)[0].id == "f_gi"


def test_chunk_label_front_matter_and_split():
    text = "---\nverified: true\n---\n# 适应症\n" + "本品用于体重管理。" * 5 + "\n\n## 用法用量\n" + "每周一次皮下注射。" * 5
    verified, chunks = chunk_label(text)
    assert verified is True and len(chunks) == 2 and chunks[0].startswith("# 适应症")


def test_chunk_label_unverified_by_default():
    verified, chunks = chunk_label("# 标题\n" + "内容很长" * 10)
    assert verified is False and len(chunks) == 1


def test_chroma_store_if_installed(tmp_path):
    pytest.importorskip("chromadb")
    from app.rag.store import ChromaStore

    k = KnowledgeBase(embedder=HashEmbedding(), store=ChromaStore(str(tmp_path / "c")))
    k.index_facts(FACTS)
    assert k.retrieve("司美格鲁肽 头对头", k=2)[0].id == "f_dreams3"
    assert all(c.verified for c in k.retrieve("研究", k=5, only_verified=True))
