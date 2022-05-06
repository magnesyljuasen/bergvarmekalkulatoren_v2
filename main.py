import streamlit as st
from utilities import Dimensjonering, Forside, Gis, Energibronn, Strompriser, Temperaturdata, Energibehov, Kostnader, Co2, Veienvidere

forside_obj = Forside()
forside_obj.innstillinger()

def main ():   
    forside_obj.forsidebilde()
    st.title (forside_obj.overskrift())
    adresse, bolig_areal = forside_obj.input()
    
    press_start = forside_obj.start_button()
    if "load_state" not in st.session_state:
        st.session_state.load_state = False
    if press_start or st.session_state.load_state:
        st.session_state.load_state = True

        #-----Session state-----
        st.markdown("""---""")
        st.title('Grunnlag')
        st.header('Innhenter data for ' + str (adresse))
        adresse_lat, adresse_long = Gis().adresse_til_koordinat(adresse)
        dybde_til_fjell, energibronn_lat, energibronn_long = Energibronn(adresse_lat, adresse_long).dybde_til_fjell()
        temperaturdata_obj = Temperaturdata(adresse_lat,adresse_long)
        stasjon_id, stasjon_lat, stasjon_long, distanse_min = temperaturdata_obj.nearmeste_stasjon()
        #st.write (temperaturdata_obj.gjennomsnittstemperatur())
        Gis().kart(stasjon_lat, adresse_lat, energibronn_lat, stasjon_long, adresse_long, energibronn_long)
        with st.expander ('Hva viser kartet?'):
            st.write (""" Kartet viser adresse, nærmeste eksisterende energibrønn og nærmeste værstasjon med fullstendige. 
            Nærmeste eksisterende energibrønn brukes til å estimere dybde til fjell i området. 
            Fra værstasjonen hentes det inn målt temperatur per time for de siste 4 år. """)
        
        st.header('Beregner oppvarmingsbehov for din bolig')
        with st.expander ('Hvordan beregnes oppvarmingsbehovet?'):
            st.write (""" Gjennomsnittstemperatur fra de siste 4 år og oppgitt boligareal benyttes til å estimere 
            oppvarmingsbehovet for din bolig. Beregningen gjøres ved hjelp av PROFet som er utviklet av Sintef. 
            Verktøyet estimerer både det årlige behovet for romoppvarming- og varmtvann som til sammen
            utgjør det totale årlige oppvarmingsbehovet for din bolig. """)
        energibehov_obj = Energibehov()
        dhw_arr, romoppvarming_arr = energibehov_obj.totalt_behov_fra_fil(stasjon_id, bolig_areal)
        dhw_sum, romoppvarming_sum, energibehov_sum = energibehov_obj.aarlig_behov(dhw_arr, romoppvarming_arr)
        dhw_sum, romoppvarming_sum, dhw_arr, romoppvarming_arr = energibehov_obj.juster_behov(dhw_sum, romoppvarming_sum, dhw_arr, romoppvarming_arr)
        energibehov_obj.resultater(dhw_sum, romoppvarming_sum, energibehov_sum)
        energibehov_obj.plot(dhw_arr, romoppvarming_arr)
        energibehov_arr = (dhw_arr + romoppvarming_arr).reshape(-1)

        st.title('Dimensjonering') 
        with st.expander ('Velg betingelser for dimensjoneringen'):
            st.write(""" For å dimensjonere ditt bergvarmeanlegg må du angi dekningsgraden til anlegget. Vanligvis settes
            #dekningsgraden til 100% som betyr at bergvarmeanlegget skal dimensjoneres for å dekke hele 
            #energibehovet. Spisslasten må dekkes av noe annet enn bergvarmeanlegget som f.eks. vedfyring eller strøm. """)
            dimensjonering_obj = Dimensjonering()       
            dekningsgrad = dimensjonering_obj.angi_dekningsgrad()
            st.write (""" Teoretisk årsvarmefaktor (Seasonal Coefficient of Performance) finner du på varmepumpens energimerke. 
            SCOP er beregnet ut fra fabrikkdata. Den angir hvor mye mer varme en varmepumpe i beste fall kan levere, 
            sammenlignet med hva den bruker i strøm. I praksis er det vanskelig å oppnå så høye tall – 
            og dermed strømsparing – i virkeligheten.""")
            cop = dimensjonering_obj.angi_cop()
        energibehov_arr_gv, energibehov_sum_gv, varmepumpe_storrelse = dimensjonering_obj.energi_og_effekt_beregning(dekningsgrad, cop, energibehov_arr, energibehov_sum)
        levert_fra_bronner_arr, kompressor_arr, spisslast_arr, levert_fra_bronner_sum, kompressor_sum, spisslast_sum = dimensjonering_obj.dekning(energibehov_arr_gv, energibehov_arr, cop)
        dimensjonering_obj.energi_resultater(levert_fra_bronner_sum, kompressor_sum, spisslast_sum)
        dimensjonering_obj.varighetsdiagram_bar(spisslast_arr, energibehov_arr_gv, kompressor_arr, levert_fra_bronner_arr)
        antall_meter = dimensjonering_obj.antall_meter(varmepumpe_storrelse, levert_fra_bronner_sum, cop)
        antall_bronner = dimensjonering_obj.antall_bronner (antall_meter)

        st.title ('Anbefalinger')
        dimensjonering_obj.bronn_resultater(antall_meter, varmepumpe_storrelse, antall_bronner)

        st.title ('Kostnadsanalyse')
        strompriser_obj = Strompriser()
        with st.expander ('Velg betingelser for kostnadsanalysen'):
            strompriser_obj.input()
            el_pris = strompriser_obj.beregn_el_pris()
            kostnader_obj = Kostnader(dybde_til_fjell, varmepumpe_storrelse, antall_meter, kompressor_arr, energibehov_arr_gv, el_pris)
            kostnader_obj.oppdater_dybde_til_fjell()

        st.header ('Bergvarme reduserer dine månedlige utgifter')
        kostnader_obj.monthly_costs()

        st.header ('Investeringskostnad')
        st.write (""" Den største barrieren når det gjelder etablering av bergvarmeanlegg er investeringskostnaden.
        Investeringskostnaden inkluderer boring av energibrønn samt installasjon av varmepumpe. """)
        kostnader_obj.plot_investeringskostnad()

        st.header ('Grønne lån')
        st.write (""" Grønne energilån er lån til bærekraftige formål som for eksempel etablering av et bergvarmeanlegg.
        Du kan dermed låne penger til å dekke investeringskostnaden. I grafen under kan du justere låneparameterene 
        nedbetalingstid og effektiv rente, for så å få ut den årlige kostnadsutviklingen. """)
        with st.expander ('Velg betingselser for beregningen'):
            kostnader_obj.gronne_laan()

        st.header ('Et miljøvennlig alternativ')
        st.write (""" Figuren under viser forbruk av CO2 med et bergvarmeanlegg kontra elektrisk oppvarming. """)
        Co2().beregning(energibehov_arr, kompressor_sum)
        
        st.markdown("""---""")
        Veienvidere()
        st.caption('Copyright ©️2022, Asplan Viak AS')
        #-----------------------
        
main ()
