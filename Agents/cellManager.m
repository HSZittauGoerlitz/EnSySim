classdef cellManager < handle
    %CELLMANAGER Manages all agent types of his cell
    %   The cellular approach divides the energy system into several energy cells.
    %   According to this approach the energy system of ensysim is build up. The
    %   cell manager agent represents such an energy cell and registers the energy
    %   loads of all agents attached to his cell.

    properties
        % number of specific agents
        nBSLconsumer_e
        nPHHconsumer_e
        % agent objects
        BSLconsumer_e
        PHHconsumer_e
        % resulting balance
        currentEnergyBalance_e  % Wh
        currentEnergyBalance_t  % Wh
    end

    methods
        function self = cellManager(nBSLconsumer_e, nPHHconsumer_e, ...
                                    pAgriculture, ...
                                    normSLP, ...
                                    BSL_COC_distribution, PHH_COC_distribution)
            % check input parameter
            if pAgriculture < 0 || pAgriculture > 1
               error("pAgriculture must be a number between 0 and 1!");
            end
                                
            self.nBSLconsumer_e = nBSLconsumer_e;
            self.nPHHconsumer_e = nPHHconsumer_e;
            self.BSLconsumer_e = BSLconsumer_e(self.nBSLconsumer_e, pAgriculture, ...
                                               normSLP, BSL_COC_distribution);
            self.PHHconsumer_e = PHHconsumer_e(self.nPHHconsumer_e, ...
                                               normSLP, PHH_COC_distribution);
            self.currentEnergyBalance_e = 0;
        end

        function self = update(self, timeIdx)
            self.BSLconsumer_e.update(timeIdx);
            self.PHHconsumer_e.update(timeIdx);
            self.currentEnergyBalance_e = self.BSLconsumer_e.currentEnergyBalance_e + ...
                                          self.PHHconsumer_e.currentEnergyBalance_e;
        end
    end
end

