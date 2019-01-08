#include "Gadget.hpp"
#include "Architecture.hpp"
#include "Expression.hpp"

// Constructor 
Gadget::Gadget(int id, IRBlock* irblock): _id(id){
    vector<reg_pair>::iterator reg_it; 
    vector<SPair>::iterator spair_it; 
    vector<SPair>* p;
    int i;
    bool is_inc;
    cst_t inc;
    
    // Get the semantics 
    _semantics = irblock->compute_semantics();
    //_semantics->simplify_expressions(); 
    //s_semantics->simplify_conditions(); 
    //debug
    
    // Set the different fields 
    // Get the registers that have been modified 
    for( i = 0; i < NB_REGS_MAX; i++)
        _reg_modified[i] = irblock->reg_modified(i); 
        
    // Get the sp_inc 
    _known_sp_inc = false; 
    if( (p = _semantics->get_reg(curr_arch()->sp())) != nullptr){
        for( spair_it = p->begin(); spair_it != p->end(); spair_it++){
            if( spair_it->cond_ptr()->is_true() ){
                std::tie(is_inc, inc) = spair_it->expr_ptr()->is_reg_increment(curr_arch()->sp());
                if( is_inc ){
                    _sp_inc = inc; 
                    _known_sp_inc = true; 
                    break;
                }
            }
        }
    }else{
        _known_sp_inc = true;
        _sp_inc = 0; 
    }
    // Get the memory reads and writes from the irblock 
    _mem_read = irblock->mem_reads();
    _mem_write = irblock->mem_writes();
    // Get the return type 
    // TODO 
}

// Accessors 
int Gadget::id(){return _id;}
GadgetType Gadget::type(){return _type;}
vector<addr_t>* Gadget::addresses(){return &_addresses;}
string Gadget::asm_str(){return _asm_str;}
string Gadget::hex_str(){return _hex_str;}
int Gadget::nb_instr(){return _nb_instr;}
int Gadget::nb_instr_ir(){return _nb_instr_ir;}
int Gadget::sp_inc(){return _sp_inc;}
bool Gadget::known_sp_inc(){return _known_sp_inc;}
vector<ExprObjectPtr>* Gadget::mem_read(){return &_mem_read;} 
vector<ExprObjectPtr>* Gadget::mem_write(){return &_mem_write;} 
RetType Gadget::ret_type(){return _ret_type;}
Semantics* Gadget::semantics(){return _semantics;}
// Modifiers
void Gadget::add_address(addr_t addr){
    _addresses.push_back(addr);
}

// Destructor 
Gadget::~Gadget(){
    delete _semantics; 
}
// Other
void Gadget::print(ostream& os){
    int i;
    vector<addr_t>::iterator it; 
    vector<ExprObjectPtr>::iterator pit; 
    os << "Gadget" << endl; 
    os << "\tAssembly: " << _asm_str << endl; 
    os << "\tHex: " << _hex_str << endl; 
    os << "\tAvailable addresses: "; 
    for( it = _addresses.begin(); it != _addresses.end(); it++)
        os << *it; // TODO, format hex 
    os << endl; 
    if( _known_sp_inc )
        os << "\tSP increment: " << _sp_inc << endl; 
    else
        os << "\tSP increment: Unknown" << endl; 
    os << "\tReading memory at: ";
    for( pit = _mem_read.begin(); pit != _mem_read.end(); pit++)
        os << "\n\t\t" << *pit; 
    os << endl; 
    os << "\tWriting memory at: ";
    for( pit = _mem_write.begin(); pit != _mem_write.end(); pit++)
        os << "\n\t\t" << *pit; 
    os << endl; 
    os << "\tModified registers: ";
    for( i = 0; i < NB_REGS_MAX; i++)
        if( _reg_modified[i])
            os << i << " "; 
    os << endl; 
}
bool Gadget::lthan(Gadget* other){
    if( _known_sp_inc && other->known_sp_inc() &&
        _sp_inc < other->sp_inc() )
        return true; 
    if( _nb_instr == other->nb_instr() )
        return _nb_instr_ir < other->nb_instr_ir();
    return _nb_instr < other->nb_instr(); 
}

ostream& operator<<(ostream& os, Gadget* g){
    g->print(os); 
    return os;
}